import time
import io
import uuid
from PIL import Image
from watermark.embed import embed_watermark
from watermark.extract_crop_optimized import extract_watermark_crop_search

def test_worst_case_crop():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    img = Image.open(path).convert("RGB")
    protected = embed_watermark(img, uuid.uuid4())
    
    w, h = 512, 512
    crop_w, crop_h = 435, 435
    
    # We want a candidate that is NOT an anchor and NOT around an anchor.
    # dx_max = 77, dy_max = 77.
    # Center is 38. Corners are 0, 77.
    # Let's use dx=60, dy=60.
    left = 60
    top = 60
    c = protected.crop((left, top, left + crop_w, top + crop_h))
    
    t0 = time.time()
    verdict, uid, stats = extract_watermark_crop_search(c)
    print(f"Worst Case Crop (dx=60, dy=60) took {time.time()-t0:.2f}s, verdict: {verdict}")
    print(f"Stats: {stats}")

if __name__ == "__main__":
    test_worst_case_crop()
