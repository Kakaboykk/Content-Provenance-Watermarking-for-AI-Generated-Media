import time
from PIL import Image
import numpy as np
import io
import sys

from watermark.extract import extract_watermark_full
from watermark.preprocess import preprocess_image

def analyze():
    file_path = r"C:\Users\priti\Downloads\gen image\beachside protected 15.png"
    
    with open(file_path, "rb") as f:
        raw_bytes = f.read()
        
    img = Image.open(io.BytesIO(raw_bytes))
    print("--- 1. UPLOADED FILE PROPERTIES ---", flush=True)
    print(f"Format: {img.format}", flush=True)
    print(f"Mode: {img.mode}", flush=True)
    print(f"Size: {img.size}", flush=True)
    
    print("\n--- 2. DIMENSIONS BEFORE EXTRACTION STAGES ---", flush=True)
    img_rgb = img.convert("RGB")
    print(f"Before extract_watermark_full: {img_rgb.size}", flush=True)
    
    w, h = img_rgb.size
    print(f"Width: {w}, Height: {h}", flush=True)

if __name__ == "__main__":
    analyze()
