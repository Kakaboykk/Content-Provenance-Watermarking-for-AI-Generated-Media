import cv2
import numpy as np

def simulate():
    total_blocks = 1024
    blocks_per_rs = 192
    repetitions = 5
    
    missing_mask = np.zeros((32, 32), dtype=bool)
    missing_mask[:, :2] = True  # left 38 / 16 = 2.3 blocks
    missing_mask[:, -3:] = True # right 38 / 16 = 2.3 blocks
    missing_mask[:2, :] = True  # top 38 / 16 = 2.3 blocks
    missing_mask[-3:, :] = True # bottom 38 / 16 = 2.3 blocks
    
    missing_indices = []
    for r in range(32):
        for c in range(32):
            if missing_mask[r, c]:
                missing_indices.append(r * 32 + c)
                
    missing_set = set(missing_indices)
    print(f"Missing blocks: {len(missing_set)} / 1024 ({(len(missing_set)/1024)*100:.2f}%)")
    
    import random
    rng = random.Random(0x574D5031)
    indices = list(range(1024))
    rng.shuffle(indices)
    
    bits = np.zeros((repetitions, 384), dtype=int)
    
    for c_idx in range(repetitions):
        start = c_idx * blocks_per_rs
        end = start + blocks_per_rs
        copy_blocks = indices[start:end]
        
        for k, b in enumerate(copy_blocks):
            if b in missing_set:
                bits[c_idx, 2*k] = 1
                bits[c_idx, 2*k+1] = 1
                
    errors = 0
    for i in range(384):
        votes = np.sum(bits[:, i])
        if votes >= 3:
            errors += 1
            
    print(f"Total bit errors after majority vote: {errors} / 384 ({(errors/384)*100:.2f}%)")

if __name__ == "__main__":
    simulate()
