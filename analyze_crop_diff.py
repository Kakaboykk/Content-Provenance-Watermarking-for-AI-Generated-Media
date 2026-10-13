import cv2
import numpy as np
from PIL import Image

def analyze_crop():
    original_path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    cropped_path = r"C:\Users\priti\Downloads\gen image\beachside protected 15.png"
    
    orig = Image.open(original_path).convert("RGB")
    crop = Image.open(cropped_path).convert("RGB")
    
    orig_np = np.array(orig)
    crop_np = np.array(crop)
    
    print(f"Original size: {orig.size}")
    print(f"Crop size: {crop.size}")
    
    # Use cv2 matchTemplate to find the exact crop coordinates
    res = cv2.matchTemplate(orig_np, crop_np, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    
    top_left = max_loc
    print(f"Best match found at (dx, dy): {top_left} with confidence {max_val:.4f}")
    
    if max_val > 0.99:
        dx, dy = top_left
        cw, ch = crop.size
        
        # Extract the exact crop from the original
        synthetic_crop = orig_np[dy:dy+ch, dx:dx+cw]
        
        # Compare pixels
        diff = np.abs(synthetic_crop.astype(int) - crop_np.astype(int))
        max_diff = np.max(diff)
        mean_diff = np.mean(diff)
        
        print(f"Max pixel difference: {max_diff}")
        print(f"Mean pixel difference: {mean_diff:.4f}")
        
        if max_diff > 0:
            # How many pixels are different?
            num_diff = np.sum(diff > 0)
            total = diff.size
            print(f"Number of differing channels: {num_diff} / {total} ({(num_diff/total)*100:.2f}%)")
    else:
        print("Could not find a perfect match. The crop might be scaled or heavily modified.")

if __name__ == "__main__":
    analyze_crop()
