import cv2
import numpy as np
from PIL import Image
from watermark.preprocess import preprocess_image
from watermark.dwt import apply_dwt
from watermark.dct import apply_dct
from watermark.interleave import deinterleave
from watermark.ecc import rs_decode, ECCError
from watermark.payload import deserialize_bits_to_bytes, parse_payload_bytes, PayloadError
from watermark.config import DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
from watermark.blocks import get_copy_blocks

def qim_extract(c_extracted: float, delta: float) -> int:
    q = int(round(c_extracted / delta))
    return abs(q) % 2

def test_masked_extraction():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    
    dx = 77
    dy = 0
    crop_w = 435
    crop_h = 435
    
    c = img.crop((dx, dy, dx + crop_w, dy + crop_h))
    Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
    padded_Y = cv2.copyMakeBorder(Y, dy, 512 - crop_h - dy, dx, 512 - crop_w - dx, cv2.BORDER_REFLECT)
    
    _, (_, HL_padded, _) = apply_dwt(padded_Y)
    
    valid_mask = np.zeros((32, 32), dtype=bool)
    valid_top = dy // 16
    valid_bottom = (dy + crop_h) // 16
    valid_left = dx // 16
    valid_right = (dx + crop_w) // 16
    valid_mask[valid_top:valid_bottom, valid_left:valid_right] = True
    
    extracted_bits = [[0] * 384 for _ in range(REPETITIONS)]
    valid_votes = [[False] * 384 for _ in range(REPETITIONS)]
    
    for c_idx in range(REPETITIONS):
        copy_blocks = get_copy_blocks(c_idx)
        for k in range(BLOCKS_PER_RS_COPY):
            block_idx = copy_blocks[k]
            row, col = block_idx // 32, block_idx % 32
            block = HL_padded[row*8:row*8+8, col*8:col*8+8]
            dct_block = apply_dct(block)
            
            b0 = qim_extract(dct_block[DCT_COEFF_POS_1], DELTA_INITIAL)
            b1 = qim_extract(dct_block[DCT_COEFF_POS_2], DELTA_INITIAL)
            extracted_bits[c_idx][2*k] = b0
            extracted_bits[c_idx][2*k+1] = b1
            
            if valid_mask[row, col]:
                valid_votes[c_idx][2*k] = True
                valid_votes[c_idx][2*k+1] = True
                
    majority_bits = [0] * 384
    for i in range(384):
        votes = sum(extracted_bits[c][i] for c in range(REPETITIONS) if valid_votes[c][i])
        total_votes = sum(valid_votes[c][i] for c in range(REPETITIONS))
        
        if total_votes > 0:
            majority_bits[i] = 1 if votes >= (total_votes / 2.0) else 0
        else:
            # Fallback to standard vote if all copies are missing
            v = sum(extracted_bits[c][i] for c in range(REPETITIONS))
            majority_bits[i] = 1 if v >= 3 else 0
            
    deinterleaved_bits = deinterleave(majority_bits)
    candidate_bytes = deserialize_bits_to_bytes(deinterleaved_bits)
    
    try:
        decoded_bytes = rs_decode(candidate_bytes)
        print("ECC SUCCESS!")
        parse_payload_bytes(decoded_bytes)
        print("CRC SUCCESS!")
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    test_masked_extraction()
