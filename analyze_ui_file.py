import time
from PIL import Image
import numpy as np
import io

from watermark.extract import extract_watermark_full
from watermark.preprocess import preprocess_image

def analyze():
    # 1. The actual UI uploaded file
    file_path = r"C:\Users\priti\Downloads\gen image\beachside protected 15.png"
    
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
        
    img = Image.open(io.BytesIO(raw_bytes))
    print("--- 1. UPLOADED FILE PROPERTIES ---")
    print(f"Format: {img.format}")
    print(f"Mode: {img.mode}")
    print(f"Size: {img.size}")
    
    # 2. Dimensions immediately before extraction stages
    print("\n--- 2. DIMENSIONS BEFORE EXTRACTION STAGES ---")
    img_rgb = img.convert("RGB")
    print(f"Before extract_watermark_full: {img_rgb.size}")
    
    # Let's see what happens inside extract_watermark_full
    w, h = img_rgb.size
    print(f"Before extract_watermark_crop_search (since w < 512 or h < 512): {img_rgb.size}")
    
    # Inside extract_watermark_crop_search: preprocess_image is called
    Y, _, _ = preprocess_image(img_rgb, target_size=(w, h))
    print(f"Before fast_extract_from_Y: Preprocessed Y shape: {Y.shape}")
    
    # 8. Run extract_watermark_full
    print("\n--- 8. EXTRACTION RESULTS ---")
    t0 = time.time()
    verdict, uid, stats = extract_watermark_full(img_rgb)
    t1 = time.time()
    
    print(f"Final Status: {verdict}")
    print(f"UUID: {uid}")
    print(f"Candidates Tested: {stats.get('candidates_tested', 'N/A')}")
    print(f"Extraction Time: {t1 - t0:.3f}s")
    print(f"ECC Success: {stats.get('ecc_success')}")
    print(f"CRC Success: {stats.get('crc_success')}")

if __name__ == "__main__":
    analyze()
