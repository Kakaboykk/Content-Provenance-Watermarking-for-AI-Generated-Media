import uuid
import hashlib
from typing import List, Tuple
import numpy as np
from PIL import Image

from watermark.config import (
    DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
)
from watermark.preprocess import preprocess_image, postprocess_image
from watermark.payload import create_payload_bytes, serialize_payload_to_bits
from watermark.ecc import rs_encode
from watermark.interleave import interleave
from watermark.blocks import get_copy_blocks
from watermark.dwt import apply_dwt, apply_idwt
from watermark.dct import apply_dct, apply_idct

def qim_embed(c: float, b: int, delta: float) -> float:
    """
    Embed bit `b` (0 or 1) into DCT coefficient `c` using QIM with step `delta`.
    """
    q = round(c / delta)
    if b == 1:
        if q % 2 == 0:
            q = q + 1  # force odd
    elif b == 0:
        if q % 2 == 1:
            q = q + 1  # force even
    else:
        raise ValueError("Bit must be 0 or 1")
    return q * delta

def embed_watermark(image: Image.Image, provenance_id: uuid.UUID, delta: float = DELTA_INITIAL) -> Tuple[Image.Image, str]:
    """
    Complete embedding pipeline.
    Returns:
        (watermarked_image, sha256_hash_of_png_bytes)
        The SHA256 should ideally be computed on the saved PNG bytes. We will return the image
        and let the caller save it and compute SHA256, but since the spec says "Save as lossless PNG
        -> Compute SHA-256", we can just return the PIL image and let the demo script handle saving and hashing.
    """
    # Step 1: Preprocessing
    Y, Cb, Cr = preprocess_image(image)
    
    # Step 2: Build payload
    payload_bytes = create_payload_bytes(provenance_id)
    
    # Step 3: Reed-Solomon encoding
    encoded_bytes = rs_encode(payload_bytes)
    
    # Serialize to bits (384 bits)
    encoded_bits = serialize_payload_to_bits(encoded_bytes)
    
    # Step 4: Interleaving
    interleaved_bits = interleave(encoded_bits)
    
    # Step 5: Repetition (we just use interleaved_bits 5 times logically)
    # The spec conceptually has a 1920-bit array, but we can just use the 384-bit array in a loop.
    
    # Step 7: DWT decomposition
    LL, (LH, HL, HH) = apply_dwt(Y)
    
    # We will modify HL in place. HL has shape (256, 256) for a 512x512 image.
    HL_modified = HL.copy()
    
    # Step 8: Embedding loop
    for c_idx in range(REPETITIONS):
        copy_blocks = get_copy_blocks(c_idx)
        for k in range(BLOCKS_PER_RS_COPY):
            block_idx = copy_blocks[k]
            row = block_idx // 32
            col = block_idx % 32
            
            # Extract 8x8 block from HL
            r_start, r_end = row * 8, row * 8 + 8
            c_start, c_end = col * 8, col * 8 + 8
            block = HL_modified[r_start:r_end, c_start:c_end]
            
            # Apply 2D DCT
            dct_block = apply_dct(block)
            
            # Get bits
            bit_0 = interleaved_bits[2 * k]
            bit_1 = interleaved_bits[2 * k + 1]
            
            # Modify coefficients
            dct_block[DCT_COEFF_POS_1] = qim_embed(dct_block[DCT_COEFF_POS_1], bit_0, delta)
            dct_block[DCT_COEFF_POS_2] = qim_embed(dct_block[DCT_COEFF_POS_2], bit_1, delta)
            
            # Apply IDCT and write back
            idct_block = apply_idct(dct_block)
            HL_modified[r_start:r_end, c_start:c_end] = idct_block

    # Step 9: DWT reconstruction
    Y_watermarked = apply_idwt((LL, (LH, HL_modified, HH)))
    
    # Step 10: YCbCr to RGB
    watermarked_image = postprocess_image(Y_watermarked, Cb, Cr)
    
    return watermarked_image
