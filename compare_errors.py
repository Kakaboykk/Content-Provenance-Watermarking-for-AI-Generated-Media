import cv2
import numpy as np
from PIL import Image
from watermark.preprocess import preprocess_image
from watermark.dwt import apply_dwt
from watermark.dct import apply_dct
from watermark.config import DELTA_INITIAL, DCT_COEFF_POS_1, DCT_COEFF_POS_2, REPETITIONS, BLOCKS_PER_RS_COPY
from watermark.blocks import get_copy_blocks

def qim_extract(c_extracted: float, delta: float) -> int:
    q = int(round(c_extracted / delta))
    return abs(q) % 2

def compare_errors():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    Y_orig, _, _ = preprocess_image(img)
    _, (_, HL_orig, _) = apply_dwt(Y_orig)
    
    # Extract original bits
    orig_bits = [[0] * 384 for _ in range(REPETITIONS)]
    for c_idx in range(REPETITIONS):
        copy_blocks = get_copy_blocks(c_idx)
        for k in range(BLOCKS_PER_RS_COPY):
            block_idx = copy_blocks[k]
            row, col = block_idx // 32, block_idx % 32
            block = HL_orig[row*8:row*8+8, col*8:col*8+8]
            dct_block = apply_dct(block)
            orig_bits[c_idx][2*k] = qim_extract(dct_block[DCT_COEFF_POS_1], DELTA_INITIAL)
            orig_bits[c_idx][2*k+1] = qim_extract(dct_block[DCT_COEFF_POS_2], DELTA_INITIAL)
            
    def get_errors(dx, dy, crop_w, crop_h):
        c = img.crop((dx, dy, dx + crop_w, dy + crop_h))
        Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
        padded_Y = cv2.copyMakeBorder(Y, dy, 512 - crop_h - dy, dx, 512 - crop_w - dx, cv2.BORDER_REFLECT)
        _, (_, HL_padded, _) = apply_dwt(padded_Y)
        
        bits = [[0] * 384 for _ in range(REPETITIONS)]
        for c_idx in range(REPETITIONS):
            copy_blocks = get_copy_blocks(c_idx)
            for k in range(BLOCKS_PER_RS_COPY):
                block_idx = copy_blocks[k]
                row, col = block_idx // 32, block_idx % 32
                block = HL_padded[row*8:row*8+8, col*8:col*8+8]
                dct_block = apply_dct(block)
                bits[c_idx][2*k] = qim_extract(dct_block[DCT_COEFF_POS_1], DELTA_INITIAL)
                bits[c_idx][2*k+1] = qim_extract(dct_block[DCT_COEFF_POS_2], DELTA_INITIAL)
                
        majority_errors = 0
        byte_errors = 0
        for i in range(384):
            votes = sum(bits[c][i] for c in range(REPETITIONS))
            maj_bit = 1 if votes >= 3 else 0
            
            orig_votes = sum(orig_bits[c][i] for c in range(REPETITIONS))
            orig_maj = 1 if orig_votes >= 3 else 0
            
            if maj_bit != orig_maj:
                majority_errors += 1
                
        print(f"Crop {dx},{dy}: {majority_errors} bit errors after majority vote")
        
    get_errors(38, 38, 435, 435)
    get_errors(77, 0, 435, 435)

if __name__ == "__main__":
    compare_errors()
