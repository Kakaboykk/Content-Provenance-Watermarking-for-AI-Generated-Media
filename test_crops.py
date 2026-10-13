import cv2
import numpy as np
from PIL import Image
from watermark.embed import embed_watermark
from watermark.preprocess import preprocess_image
from watermark.extract_crop_optimized import fast_extract_from_Y
from watermark.config import DELTA_INITIAL
import uuid

def test_various_crops():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    
    Y_orig, _, _ = preprocess_image(img)
    _, uid, _ = fast_extract_from_Y(Y_orig, DELTA_INITIAL)
    print(f"Original UUID: {uid}")
    
    for dx, dy in [(38, 38), (77, 0), (0, 77), (77, 77), (15, 15), (60, 60)]:
        crop_w = 512 - dx
        crop_h = 512 - dy
        c = img.crop((dx, dy, dx + crop_w, dy + crop_h))
        Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
        padded_Y = cv2.copyMakeBorder(Y, dy, 512 - crop_h - dy, dx, 512 - crop_w - dx, cv2.BORDER_REFLECT)
        verdict, uid_extracted, _ = fast_extract_from_Y(padded_Y, DELTA_INITIAL)
        print(f"Crop dx={dx}, dy={dy} verdict: {verdict}")

if __name__ == "__main__":
    test_various_crops()
