import sys
import uuid
import io
import time
from PIL import Image

from watermark.embed import embed_watermark
from watermark.extract import extract_watermark

def get_crop(img, crop_w, crop_h, pos):
    w, h = img.size
    
    if pos == "center":
        left = (w - crop_w) // 2
        top = (h - crop_h) // 2
    elif pos == "top-left" or pos == "left" or pos == "top":
        left = 0
        top = 0
    elif pos == "right":
        left = w - crop_w
        top = 0
    elif pos == "bottom":
        left = 0
        top = h - crop_h
    elif pos == "top-right":
        left = w - crop_w
        top = 0
    elif pos == "bottom-left":
        left = 0
        top = h - crop_h
    elif pos == "bottom-right":
        left = w - crop_w
        top = h - crop_h
    else:
        left = 0
        top = 0
    
    return img.crop((left, top, left + crop_w, top + crop_h))

def test():
    if len(sys.argv) < 2:
        print("Usage: python test_extract_local.py <image_path>")
        return
        
    path = sys.argv[1]
    img = Image.open(path).convert("RGB")
    
    # 1. Embed Watermark
    uid = uuid.uuid4()
    print(f"Embedding UUID: {uid}")
    watermarked_img = embed_watermark(img, uid)
    
    # 2. Test
    tests = [
        ("Original 512x512", 512, 512, "center"),
        ("Left Crop 486x512", 486, 512, "left"),
        ("Right Crop 486x512", 486, 512, "right"),
        ("Top Crop 512x486", 512, 486, "top"),
        ("Bottom Crop 512x486", 512, 486, "bottom"),
        ("Center Crop 486x486", 486, 486, "center"),
    ]
    
    for name, cw, ch, pos in tests:
        if cw == 512 and ch == 512:
            cropped = watermarked_img
        else:
            cropped = get_crop(watermarked_img, cw, ch, pos)
            
        print(f"\n--- Testing {name} ---")
        start = time.time()
        verdict, ext_uid = extract_watermark(cropped)
        elapsed = time.time() - start
        
        print(f"Final Verdict: {verdict}, UUID: {ext_uid}, Time: {elapsed:.2f}s")

if __name__ == "__main__":
    test()
