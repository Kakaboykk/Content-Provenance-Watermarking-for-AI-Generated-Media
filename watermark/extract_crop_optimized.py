import time
from watermark.preprocess import preprocess_image
from watermark.dwt import apply_dwt
from watermark.dct import apply_dct
from watermark.interleave import deinterleave
from watermark.ecc import rs_decode, ECCError
from watermark.payload import parse_payload_bytes, PayloadError, deserialize_bits_to_bytes
from watermark.config import DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
from watermark.blocks import get_copy_blocks
from typing import Tuple, Optional
import uuid
from PIL import Image
import cv2
import numpy as np

def qim_extract(c_extracted: float, delta: float) -> int:
    q = int(round(c_extracted / delta))
    return abs(q) % 2

def fast_extract_from_Y(Y: np.ndarray, delta: float) -> Tuple[str, Optional[uuid.UUID], dict]:
    stats = {"candidate_bytes": None, "ecc_success": False, "crc_success": False}
    
    _, (_, HL, _) = apply_dwt(Y)
    
    extracted_bits = [[0] * 384 for _ in range(REPETITIONS)]
    
    for c_idx in range(REPETITIONS):
        copy_blocks = get_copy_blocks(c_idx)
        for k in range(BLOCKS_PER_RS_COPY):
            block_idx = copy_blocks[k]
            row = block_idx // 32
            col = block_idx % 32
            
            r_start, r_end = row * 8, row * 8 + 8
            c_start, c_end = col * 8, col * 8 + 8
            block = HL[r_start:r_end, c_start:c_end]
            
            if block.shape != (8, 8):
                if block.size == 0:
                    bit_0, bit_1 = 0, 0
                else:
                    padded = np.zeros((8, 8), dtype=block.dtype)
                    r_valid, c_valid = block.shape
                    padded[:r_valid, :c_valid] = block
                    dct_block = apply_dct(padded)
                    bit_0 = qim_extract(dct_block[DCT_COEFF_POS_1], delta)
                    bit_1 = qim_extract(dct_block[DCT_COEFF_POS_2], delta)
            else:
                dct_block = apply_dct(block)
                bit_0 = qim_extract(dct_block[DCT_COEFF_POS_1], delta)
                bit_1 = qim_extract(dct_block[DCT_COEFF_POS_2], delta)
                
            extracted_bits[c_idx][2 * k] = bit_0
            extracted_bits[c_idx][2 * k + 1] = bit_1
            
    majority_bits = [0] * 384
    for i in range(384):
        votes = sum(extracted_bits[c][i] for c in range(REPETITIONS))
        majority_bits[i] = 1 if votes >= 3 else 0
        
    deinterleaved_bits = deinterleave(majority_bits)
    
    try:
        candidate_bytes = deserialize_bits_to_bytes(deinterleaved_bits)
        stats["candidate_bytes"] = candidate_bytes
    except ValueError:
        return "WATERMARK_UNRECOVERABLE", None, stats
        
    try:
        decoded_bytes = rs_decode(candidate_bytes)
        stats["ecc_success"] = True
    except ECCError:
        return "WATERMARK_UNRECOVERABLE", None, stats
        
    try:
        provenance_id = parse_payload_bytes(decoded_bytes)
        stats["crc_success"] = True
    except PayloadError:
        return "NO_WATERMARK_FOUND", None, stats
        
    return "AUTHENTIC_UNMODIFIED", provenance_id, stats

def extract_watermark_crop_search(image: Image.Image, delta: float = DELTA_INITIAL, best_verdict="NO_WATERMARK_FOUND") -> Tuple[str, Optional[uuid.UUID], dict]:
    w, h = image.size
    
    CROP_SEARCH_MAX_PERCENT = 20 # increased to allow 15% crop
    min_dim = 512 * (100 - CROP_SEARCH_MAX_PERCENT) // 100
    if w < min_dim or h < min_dim:
        return best_verdict, None, {}
        
    dx_max = 512 - w
    dy_max = 512 - h
    
    candidates = []
    
    # 1. Exact geometric anchors
    # Center
    c_dx = dx_max // 2
    c_dy = dy_max // 2
    anchors = [(c_dx, c_dy)]
    
    # Edges
    if dx_max > 0:
        anchors.extend([(0, c_dy), (dx_max, c_dy)]) # Left, Right
    if dy_max > 0:
        anchors.extend([(c_dx, 0), (c_dx, dy_max)]) # Top, Bottom
        
    # Corners
    if dx_max > 0 and dy_max > 0:
        anchors.extend([(0, 0), (dx_max, 0), (0, dy_max), (dx_max, dy_max)])
        
    for a in anchors:
        if a not in candidates:
            candidates.append(a)
            
    # 2. Likely integer-aligned offsets around anchors (e.g. +/- 1, 2)
    # This catches off-by-one errors from manual crops
    for ax, ay in list(candidates):
        for ox in [-2, -1, 1, 2]:
            for oy in [-2, -1, 1, 2]:
                nx, ny = ax + ox, ay + oy
                if 0 <= nx <= dx_max and 0 <= ny <= dy_max:
                    if (nx, ny) not in candidates:
                        candidates.append((nx, ny))
                        
    # 3. Bounded sweep for remaining possibilities
    # We only sweep if we haven't found it in the anchors.
    # To avoid testing 6000 candidates unnecessarily, we can sweep sparsely first,
    # or just do a full sweep since we optimized the inner loop.
    sweep = []
    for dy in range(0, dy_max + 1):
        for dx in range(0, dx_max + 1):
            if (dx, dy) not in candidates:
                sweep.append((dx, dy))
                
    candidates.extend(sweep)
    
    # Optimize: Precompute Y channel to avoid cv2.cvtColor in the loop
    Y, _, _ = preprocess_image(image, target_size=(w, h))
    
    import time
    t0 = time.time()
    tested_count = 0
    
    best_stats = {}
    
    for dx, dy in candidates:
        tested_count += 1
        top = dy
        bottom = 512 - h - dy
        left = dx
        right = 512 - w - dx
        
        # Pad Y directly
        padded_Y = cv2.copyMakeBorder(Y, top, bottom, left, right, cv2.BORDER_REFLECT)
        
        verdict, uid, stats = fast_extract_from_Y(padded_Y, delta)
        
        if verdict in ("AUTHENTIC_UNMODIFIED", "TRACED_BUT_MODIFIED"):
            stats["candidates_tested"] = tested_count
            stats["extraction_time_sec"] = time.time() - t0
            return verdict, uid, stats
            
        if verdict == "WATERMARK_UNRECOVERABLE" and best_verdict == "NO_WATERMARK_FOUND":
            best_verdict = verdict
            best_stats = stats
            
        # Hard timeout at 45 seconds to prevent 504 Gateway Timeout
        if time.time() - t0 > 45.0:
            break
            
    best_stats["candidates_tested"] = tested_count
    best_stats["extraction_time_sec"] = time.time() - t0
    return best_verdict, None, best_stats
