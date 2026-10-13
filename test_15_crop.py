import time
import io
import uuid
import numpy as np
from PIL import Image
from watermark.embed import embed_watermark
from watermark.extract import extract_watermark_crop_search

def test_15_crop():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    img = Image.open(path).convert("RGB")
    protected = embed_watermark(img, uuid.uuid4())
    
    # EXACT center 15% crop (435x435)
    w, h = 512, 512
    crop_w, crop_h = 435, 435
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    c = protected.crop((left, top, left + crop_w, top + crop_h))
    
    t0 = time.time()
    verdict, uid, stats = extract_watermark_crop_search(c)
    print(f"Center Crop 435x435 took {time.time()-t0:.2f}s, verdict: {verdict}")

if __name__ == "__main__":
    test_15_crop()
