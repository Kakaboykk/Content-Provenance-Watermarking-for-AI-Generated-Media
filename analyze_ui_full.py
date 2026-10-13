import time
from PIL import Image
import numpy as np
import io
import sys
import cv2

from watermark.extract_crop_optimized import fast_extract_from_Y
from watermark.preprocess import preprocess_image
from watermark.config import DELTA_INITIAL

def analyze_full():
    file_path = r"C:\Users\priti\Downloads\gen image\beachside protected 15.png"
    
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
        
    img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    w, h = img.size
    dx_max = 512 - w
    dy_max = 512 - h
    
    Y, _, _ = preprocess_image(img, target_size=(w, h))
    
    print(f"Starting full sweep without timeout for {w}x{h} crop...", flush=True)
    t0 = time.time()
    
    for dy in range(0, dy_max + 1):
        for dx in range(0, dx_max + 1):
            top = dy
            bottom = 512 - h - dy
            left = dx
            right = 512 - w - dx
            
            padded_Y = cv2.copyMakeBorder(Y, top, bottom, left, right, cv2.BORDER_REFLECT)
            verdict, uid, stats = fast_extract_from_Y(padded_Y, DELTA_INITIAL)
            
            if verdict == "AUTHENTIC_UNMODIFIED" or verdict == "TRACED_BUT_MODIFIED":
                print(f"FOUND IT! dx={dx}, dy={dy}")
                print(f"Time: {time.time()-t0:.2f}s")
                return
    
    print("FINISHED SWEEP! Not found!")

if __name__ == "__main__":
    analyze_full()
