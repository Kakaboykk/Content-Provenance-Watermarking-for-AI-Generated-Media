import asyncio
import io
import time
import httpx
from PIL import Image
import numpy as np
import cv2
from watermark.extract import extract_watermark_with_stats

def test_manual():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    from watermark.embed import embed_watermark
    import uuid
    img = Image.open(path).convert("RGB")
    protected = embed_watermark(img, uuid.uuid4())
    
    w, h = protected.size
    
    # Crop L=25, R=1
    c = protected.crop((25, 0, w-1, h))
    
    # Manual pad L=25, R=1
    img_np = np.array(c.convert("RGB"))
    padded_np = cv2.copyMakeBorder(img_np, 0, 0, 25, 1, cv2.BORDER_REFLECT)
    padded = Image.fromarray(padded_np)
    
    verdict, uid, stats = extract_watermark_with_stats(padded, target_size=(512, 512))
    print(f"Manual padded dx=25: {verdict}")

if __name__ == "__main__":
    test_manual()
