import cv2
import numpy as np

def simulate():
    total_blocks = 1024
    blocks_per_rs = 192
    repetitions = 5
    
    missing_cols = 5  # roughly 4.8 blocks
    
    missing_mask = np.zeros((32, 32), dtype=bool)
    missing_mask[:, :missing_cols] = True
    
    missing_indices = []
    for r in range(32):
        for c in range(32):
            if missing_mask[r, c]:
                missing_indices.append(r * 32 + c)
                
    missing_set = set(missing_indices)
    
    import random
    rng = random.Random(0x574D5031)
    indices = list(range(1024))
    rng.shuffle(indices)
    
    # 384 bits per copy
    bits = np.zeros((repetitions, 384), dtype=int)
    
    for c_idx in range(repetitions):
        start = c_idx * blocks_per_rs
        end = start + blocks_per_rs
        copy_blocks = indices[start:end]
        
        for k, b in enumerate(copy_blocks):
            if b in missing_set:
                bits[c_idx, 2*k] = 1
                bits[c_idx, 2*k+1] = 1
                
    # Majority vote
    errors = 0
    for i in range(384):
        votes = np.sum(bits[:, i])
        if votes >= 3:
            errors += 1
            
    print(f"Total bit errors after majority vote: {errors} / 384 ({(errors/384)*100:.2f}%)")

if __name__ == "__main__":
    simulate()
