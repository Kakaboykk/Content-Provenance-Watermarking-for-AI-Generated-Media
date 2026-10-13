import time
import io
import uuid
import numpy as np
import cv2
from PIL import Image
from watermark.embed import embed_watermark
from watermark.preprocess import preprocess_image
from watermark.dwt import apply_dwt
from watermark.dct import apply_dct
from watermark.interleave import deinterleave
from watermark.ecc import rs_decode, ECCError
from watermark.payload import parse_payload_bytes, PayloadError, deserialize_bits_to_bytes
from watermark.config import DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
from watermark.blocks import get_copy_blocks

def qim_extract(c_extracted, delta):
    q = int(round(c_extracted / delta))
    return abs(q) % 2

def fast_extract(Y, delta=DELTA_INITIAL):
    # DWT
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
    except ValueError:
        return "WATERMARK_UNRECOVERABLE", None
        
    try:
        decoded_bytes = rs_decode(candidate_bytes)
    except ECCError:
        return "WATERMARK_UNRECOVERABLE", None
        
    try:
        provenance_id = parse_payload_bytes(decoded_bytes)
    except PayloadError:
        return "NO_WATERMARK_FOUND", None
        
    return "AUTHENTIC_UNMODIFIED", provenance_id

def test_fast_extract():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    img = Image.open(path).convert("RGB")
    protected = embed_watermark(img, uuid.uuid4())
    
    w, h = 512, 512
    crop_w, crop_h = 435, 435
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    c = protected.crop((left, top, left + crop_w, top + crop_h))
    
    Y, _, _ = preprocess_image(c)
    
    t0 = time.time()
    for _ in range(100):
        padded_Y = cv2.copyMakeBorder(Y, top, 512 - crop_h - top, left, 512 - crop_w - left, cv2.BORDER_REFLECT)
        verdict, _ = fast_extract(padded_Y)
    print(f"100 iterations took {time.time()-t0:.2f}s, verdict: {verdict}")

if __name__ == "__main__":
    test_fast_extract()
