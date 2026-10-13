import time
import uuid
from PIL import Image
import numpy as np
import cv2

from watermark.embed import embed_watermark
from watermark.extract_crop_optimized import fast_extract_from_Y
from watermark.preprocess import preprocess_image
from watermark.config import DELTA_INITIAL

def test_77_0_crop():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    
    # Crop dx=77, dy=0
    crop_w, crop_h = 435, 435
    left = 77
    top = 0
    c = img.crop((left, top, left + crop_w, top + crop_h))
    
    Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
    
    padded_Y = cv2.copyMakeBorder(Y, top, 512 - crop_h - top, left, 512 - crop_w - left, cv2.BORDER_REFLECT)
    
    verdict, uid, stats = fast_extract_from_Y(padded_Y, DELTA_INITIAL)
    print(f"Crop (dx={left}, dy={top}) verdict: {verdict}")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    test_77_0_crop()
