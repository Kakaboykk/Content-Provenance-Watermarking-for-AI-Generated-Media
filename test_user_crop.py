import cv2
import numpy as np
import time
from PIL import Image
from watermark.preprocess import preprocess_image
from watermark.extract import fast_extract_from_Y
from watermark.config import DELTA_INITIAL

def test_user_crop():
    path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(path).convert("RGB")
    
    crop_w, crop_h = 435, 435
    dx = 77
    dy = 0
    
    c = img.crop((dx, dy, dx + crop_w, dy + crop_h))
    
    t0 = time.time()
    Y, _, _ = preprocess_image(c, target_size=(crop_w, crop_h))
    padded_Y = cv2.copyMakeBorder(Y, dy, 512 - crop_h - dy, dx, 512 - crop_w - dx, cv2.BORDER_REFLECT)
    
    import math
    valid_mask = np.zeros((32, 32), dtype=bool)
    valid_top = int(math.ceil(dy / 16.0))
    valid_bottom = int(math.floor((dy + crop_h) / 16.0))
    valid_left = int(math.ceil(dx / 16.0))
    valid_right = int(math.floor((dx + crop_w) / 16.0))
    valid_mask[valid_top:valid_bottom, valid_left:valid_right] = True
    
    verdict, uid, stats = fast_extract_from_Y(padded_Y, DELTA_INITIAL, valid_mask=valid_mask)
    t1 = time.time()
    
    print(f"Time: {t1-t0:.4f}s")
    print(f"Verdict: {verdict}")
    print(f"UUID: {uid}")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    test_user_crop()
