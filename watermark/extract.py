import uuid
from typing import List, Optional, Tuple
from PIL import Image

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
    Complete blind extraction pipeline.
    Returns:
        (verdict_string, extracted_uuid)
    """
    verdict, extracted_id, _ = extract_watermark_with_stats(image, delta)
    return verdict, extracted_id

def extract_watermark_with_stats(image: Image.Image, delta: float = DELTA_INITIAL) -> Tuple[str, Optional[uuid.UUID], dict]:
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
    Y, _, _ = preprocess_image(image)
    
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
            
            # Extract 8x8 block from HL
            r_start, r_end = row * 8, row * 8 + 8
            c_start, c_end = col * 8, col * 8 + 8
            block = HL[r_start:r_end, c_start:c_end]
            
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
