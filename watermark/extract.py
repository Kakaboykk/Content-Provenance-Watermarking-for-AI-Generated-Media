import uuid
from typing import List, Optional, Tuple
from PIL import Image
import numpy as np

from watermark.config import (
    DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
)
from watermark.preprocess import preprocess_image
from watermark.blocks import get_copy_blocks
from watermark.dwt import apply_dwt
from watermark.dct import apply_dct
from watermark.interleave import deinterleave
from watermark.ecc import rs_decode, ECCError
from watermark.payload import parse_payload_bytes, PayloadError, deserialize_bits_to_bytes

def qim_extract(c_extracted: float, delta: float) -> int:
    """
    Extract bit from DCT coefficient using QIM with step `delta`.
    """
    q = int(round(c_extracted / delta))
    return abs(q) % 2

def extract_watermark(image: Image.Image, delta: float = DELTA_INITIAL) -> Tuple[str, Optional[uuid.UUID]]:
    """
    Complete blind extraction pipeline. Uses scale-search and crop-search
    if image dimensions differ from 512x512 or if the baseline extraction fails.
    Returns:
        (verdict_string, extracted_uuid)
    """
    verdict, extracted_id, _ = extract_watermark_full(image, delta)
    return verdict, extracted_id

def extract_watermark_full(image: Image.Image, delta: float = DELTA_INITIAL) -> Tuple[str, Optional[uuid.UUID], dict]:
    """
    Complete blind extraction pipeline with optimized dispatch for crops and resizes.
    """
    w, h = image.size
    
    # 1. Base Attempt
    verdict, extracted_id, stats = extract_watermark_with_stats(image, delta, target_size=(512, 512))
    if verdict in ("AUTHENTIC_UNMODIFIED", "TRACED_BUT_MODIFIED") or (w == 512 and h == 512):
        return verdict, extracted_id, stats

    # Classification
    is_crop = (w <= 512 and h <= 512) and (w == 512 or h == 512 or w > 400 and h > 400)
    # If one dimension is exactly 512, it's definitely a crop.
    # If both are < 512 but large (e.g., 486x486), it could be a center crop.
    # We will prioritize crop search for these.
    
    best_verdict = verdict
    best_uid = extracted_id
    best_stats = stats
    
    if is_crop:
        # Run crop search ONLY
        c_verdict, c_uid, c_stats = extract_watermark_crop_search(image, delta, best_verdict=best_verdict)
        if c_verdict in ("AUTHENTIC_UNMODIFIED", "TRACED_BUT_MODIFIED") or c_verdict != "NO_WATERMARK_FOUND":
            return c_verdict, c_uid, c_stats
        best_verdict = c_verdict
        best_uid = c_uid
        best_stats = c_stats
        
        # If crop search failed, and it's proportional (e.g. 460x460), maybe it WAS a resize.
        if w == h and w < 512:
            s_verdict, s_uid, s_stats = extract_watermark_scale_search(image, delta, best_verdict=best_verdict)
            return s_verdict, s_uid, s_stats
            
        return best_verdict, best_uid, best_stats

    # Otherwise (e.g. 320x320, 800x800), run scale search
    s_verdict, s_uid, s_stats = extract_watermark_scale_search(image, delta, best_verdict=best_verdict)
    return s_verdict, s_uid, s_stats

def fast_extract_from_Y(Y: np.ndarray, delta: float, valid_mask: Optional[np.ndarray] = None) -> Tuple[str, Optional[uuid.UUID], dict]:
    stats = {"candidate_bytes": None, "ecc_success": False, "crc_success": False}
    
    _, (_, HL, _) = apply_dwt(Y)
    
    extracted_bits = [[0] * 384 for _ in range(REPETITIONS)]
    valid_votes = [[True] * 384 for _ in range(REPETITIONS)]
    
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
            
            if valid_mask is not None and not valid_mask[row, col]:
                valid_votes[c_idx][2 * k] = False
                valid_votes[c_idx][2 * k + 1] = False
            
    majority_bits = [0] * 384
    for i in range(384):
        votes = sum(extracted_bits[c][i] for c in range(REPETITIONS) if valid_votes[c][i])
        total_votes = sum(valid_votes[c][i] for c in range(REPETITIONS))
        
        if total_votes > 0:
            majority_bits[i] = 1 if votes >= (total_votes / 2.0) else 0
        else:
            v = sum(extracted_bits[c][i] for c in range(REPETITIONS))
            majority_bits[i] = 1 if v >= 3 else 0
        
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
    for ax, ay in list(candidates):
        for ox in [-2, -1, 1, 2]:
            for oy in [-2, -1, 1, 2]:
                nx, ny = ax + ox, ay + oy
                if 0 <= nx <= dx_max and 0 <= ny <= dy_max:
                    if (nx, ny) not in candidates:
                        candidates.append((nx, ny))
                        
    # 3. Bounded sweep for remaining possibilities
    sweep = []
    for dy in range(0, dy_max + 1):
        for dx in range(0, dx_max + 1):
            if (dx, dy) not in candidates:
                sweep.append((dx, dy))
                
    candidates.extend(sweep)
    
    # Optimize: Precompute Y channel to avoid cv2.cvtColor in the loop
    import cv2
    import numpy as np
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
        
        import math
        valid_mask = np.zeros((32, 32), dtype=bool)
        valid_top = int(math.ceil(top / 16.0))
        valid_bottom = int(math.floor((top + h) / 16.0))
        valid_left = int(math.ceil(left / 16.0))
        valid_right = int(math.floor((left + w) / 16.0))
        valid_mask[valid_top:valid_bottom, valid_left:valid_right] = True
        
        verdict, uid, stats = fast_extract_from_Y(padded_Y, delta, valid_mask=valid_mask)
        
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


def extract_watermark_scale_search(image: Image.Image, delta: float = DELTA_INITIAL, best_verdict="NO_WATERMARK_FOUND") -> Tuple[str, Optional[uuid.UUID], dict]:
    """
    Extraction pipeline with scale search for resize robustness.
    """
    # 1. Baseline Attempt
    # Always attempt standard 512x512 extraction first
    base_verdict, base_uid, base_stats = extract_watermark_with_stats(image, delta, target_size=(512, 512))
    if base_verdict in ("AUTHENTIC_UNMODIFIED", "TRACED_BUT_MODIFIED"):
        return base_verdict, base_uid, base_stats
        
    w, h = image.size
    
    # If the image is exactly 512x512, don't run expensive scale search
    if w == 512 and h == 512:
        return base_verdict, base_uid, base_stats
        
    # 2. Configurable Scale Search
    MIN_SCALE = 0.5
    MAX_SCALE = 2.0
    SCALE_STEP = 0.05
    
    # Calculate exact inverse scale to center the search
    exact_scale = 512.0 / max(w, h)
    
    # Generate candidate scales around the inverse resize ratio
    candidate_scales = []
    
    # Search around exact scale
    for step in np.arange(-0.15, 0.16, SCALE_STEP):
        s = exact_scale + step
        if MIN_SCALE <= s <= MAX_SCALE:
            candidate_scales.append(s)
            
    # Also add some broader scales just in case
    for s in np.arange(MIN_SCALE, MAX_SCALE + SCALE_STEP, SCALE_STEP):
        if s not in candidate_scales:
            candidate_scales.append(s)
            
    # Sort candidate scales by distance to exact scale (try most likely first)
    candidate_scales.sort(key=lambda s: abs(s - exact_scale))
    
    best_verdict = base_verdict
    best_uid = base_uid
    best_stats = base_stats
    
    for s in candidate_scales:
        target_w = int(round(w * s))
        target_h = int(round(h * s))
        
        # Don't try scales that result in images too small for the 256x256 HL band
        if target_w < 256 or target_h < 256:
            continue
            
        verdict, uid, stats = extract_watermark_with_stats(image, delta, target_size=(target_w, target_h))
        print(f"[Scale Search] Scale {s:.2f} -> {target_w}x{target_h} : {verdict}", flush=True)
        
        if verdict in ("AUTHENTIC_UNMODIFIED", "TRACED_BUT_MODIFIED"):
            return verdict, uid, stats
            
        if verdict == "WATERMARK_UNRECOVERABLE" and best_verdict == "NO_WATERMARK_FOUND":
            best_verdict = verdict
            best_stats = stats
            
    return best_verdict, best_uid, best_stats

def extract_watermark_with_stats(image: Image.Image, delta: float = DELTA_INITIAL, target_size=None) -> Tuple[str, Optional[uuid.UUID], dict]:
    """
    Complete blind extraction pipeline that also returns intermediate statistics
    for evaluation (BER, ECC success, etc.).
    Returns:
        (verdict_string, extracted_uuid, stats_dict)
    """
    stats = {
        "candidate_bytes": None,
        "ecc_success": False,
        "crc_success": False,
    }
    # Step 1: Preprocessing (identical to embedding Step 1)
    # We only need the Y channel for extraction
    Y, _, _ = preprocess_image(image, target_size=target_size)
    
    # Step 2: DWT decomposition
    _, (_, HL, _) = apply_dwt(Y)
    
    # Store extracted bits: 5 copies of 384 bits each
    extracted_bits = [[0] * 384 for _ in range(REPETITIONS)]
    
    # Step 4: Extract bits
    for c_idx in range(REPETITIONS):
        copy_blocks = get_copy_blocks(c_idx)
        for k in range(BLOCKS_PER_RS_COPY):
            block_idx = copy_blocks[k]
            row = block_idx // 32
            col = block_idx % 32
            
            # Extract block from HL
            r_start, r_end = row * 8, row * 8 + 8
            c_start, c_end = col * 8, col * 8 + 8
            block = HL[r_start:r_end, c_start:c_end]
            
            # If the block is not 8x8 (happens if image is smaller than 512x512), 
            # we pad it with zeros so DCT doesn't crash, but these bits will just be noise.
            # Reed-Solomon will handle the burst errors at the boundaries.
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
                # Apply 2D DCT
                dct_block = apply_dct(block)
                # Extract bits
                bit_0 = qim_extract(dct_block[DCT_COEFF_POS_1], delta)
                bit_1 = qim_extract(dct_block[DCT_COEFF_POS_2], delta)
                
            extracted_bits[c_idx][2 * k] = bit_0
            extracted_bits[c_idx][2 * k + 1] = bit_1
            
    # Step 5: Majority vote across 5 copies
    majority_bits = [0] * 384
    for i in range(384):
        votes = sum(extracted_bits[c][i] for c in range(REPETITIONS))
        majority_bits[i] = 1 if votes >= 3 else 0
        
    # Step 6: De-interleaving
    deinterleaved_bits = deinterleave(majority_bits)
    
    # Convert bits to bytes
    try:
        candidate_bytes = deserialize_bits_to_bytes(deinterleaved_bits)
        stats["candidate_bytes"] = candidate_bytes
    except ValueError:
        return "WATERMARK_UNRECOVERABLE", None, stats
        
    # Step 7: Reed-Solomon decoding
    try:
        decoded_bytes = rs_decode(candidate_bytes)
        stats["ecc_success"] = True
    except ECCError:
        return "WATERMARK_UNRECOVERABLE", None, stats
        
    # Steps 8-10: Magic, CRC, UUID
    try:
        provenance_id = parse_payload_bytes(decoded_bytes)
        stats["crc_success"] = True
    except PayloadError:
        return "NO_WATERMARK_FOUND", None, stats
        
    return "AUTHENTIC_UNMODIFIED", provenance_id, stats
