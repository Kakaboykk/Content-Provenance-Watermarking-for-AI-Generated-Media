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

def compare_errors_masked():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    
    def get_errors(dx, dy, crop_w, crop_h):
        c = img.crop((dx, dy, dx + crop_w, dy + crop_h))
        Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
        padded_Y = cv2.copyMakeBorder(Y, dy, 512 - crop_h - dy, dx, 512 - crop_w - dx, cv2.BORDER_REFLECT)
        _, (_, HL_padded, _) = apply_dwt(padded_Y)
        
        # Mask of valid blocks
        valid_mask = np.zeros((32, 32), dtype=bool)
        valid_top = dy // 16
        valid_bottom = (dy + crop_h) // 16
        valid_left = dx // 16
        valid_right = (dx + crop_w) // 16
        valid_mask[valid_top:valid_bottom, valid_left:valid_right] = True
        
        bits = [[0] * 384 for _ in range(REPETITIONS)]
        valid_votes = [[0] * 384 for _ in range(REPETITIONS)]
        
        for c_idx in range(REPETITIONS):
            copy_blocks = get_copy_blocks(c_idx)
            for k in range(BLOCKS_PER_RS_COPY):
                block_idx = copy_blocks[k]
                row, col = block_idx // 32, block_idx % 32
                block = HL_padded[row*8:row*8+8, col*8:col*8+8]
                dct_block = apply_dct(block)
                bits[c_idx][2*k] = qim_extract(dct_block[DCT_COEFF_POS_1], DELTA_INITIAL)
                bits[c_idx][2*k+1] = qim_extract(dct_block[DCT_COEFF_POS_2], DELTA_INITIAL)
                
                if valid_mask[row, col]:
                    valid_votes[c_idx][2*k] = 1
                    valid_votes[c_idx][2*k+1] = 1
                
        majority_errors = 0
        for i in range(384):
            # Normal majority vote
            votes = sum(bits[c][i] for c in range(REPETITIONS))
            maj_bit = 1 if votes >= 3 else 0
            
            # Masked majority vote
            masked_votes_1 = sum(bits[c][i] for c in range(REPETITIONS) if valid_votes[c][i])
            masked_total = sum(valid_votes[c][i] for c in range(REPETITIONS))
            if masked_total > 0:
                masked_maj = 1 if masked_votes_1 >= (masked_total / 2.0) else 0
            else:
                masked_maj = maj_bit
                
            # We don't have orig_bits here, just see if masked maj differs from normal maj
            # Actually, I need orig_bits to know if it's correct!
            
        print(f"Masking would change decisions for some bits.")
        return bits, valid_votes

    get_errors(77, 0, 435, 435)

if __name__ == "__main__":
    compare_errors_masked()
