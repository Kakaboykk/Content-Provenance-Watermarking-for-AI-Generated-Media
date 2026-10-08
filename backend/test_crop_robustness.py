import httpx
import asyncio
import io
import sys
import time
from PIL import Image

def get_crop(img, crop_percent, pos):
    w, h = img.size
    crop_w = int(w * (1 - crop_percent/100))
    crop_h = int(h * (1 - crop_percent/100))
    
    if pos == "center":
        left = (w - crop_w) // 2
        top = (h - crop_h) // 2
    elif pos == "top-left":
        left = 0
        top = 0
    elif pos == "top-right":
        left = w - crop_w
        top = 0
    elif pos == "bottom-left":
        left = 0
        top = h - crop_h
    elif pos == "bottom-right":
        left = w - crop_w
        top = h - crop_h
    
    return img.crop((left, top, left + crop_w, top + crop_h))

async def run_tests(image_path):
    base_url = "http://127.0.0.1:8000"
    
    print(f"[1] Loading baseline image from {image_path}")
    with open(image_path, "rb") as f:
        original_img_bytes = f.read()
        
    print(f"[2] Embedding watermark via POST /watermark/embed")
    async with httpx.AsyncClient(timeout=60.0) as client:
        embed_res = await client.post(
            f"{base_url}/watermark/embed",
            files={"file": ("original.jpg", original_img_bytes, "image/jpeg")}
        )
        if embed_res.status_code != 200:
            print("Failed to embed:", embed_res.text)
            return
            
        protected_img_bytes = embed_res.content
        protected_img = Image.open(io.BytesIO(protected_img_bytes))
        
        tests = [
            ("Original", 0, "center"),
            ("Center 5%", 5, "center"),
            ("Center 10%", 10, "center"),
            ("Center 15%", 15, "center"),
            ("Center 20%", 20, "center"),
            ("Top-Left 5%", 5, "top-left"),
            ("Top-Right 5%", 5, "top-right"),
            ("Bottom-Left 5%", 5, "bottom-left"),
            ("Bottom-Right 5%", 5, "bottom-right")
        ]
        
        print(f"{'Test':<20} | {'Size':<10} | {'Verdict':<25} | {'UUID?':<6} | {'Hash?':<6} | {'Time(s)'}")
        print("-" * 85)
        
        for name, percent, pos in tests:
            if percent == 0:
                cropped = protected_img
            else:
                cropped = get_crop(protected_img, percent, pos)
                
            cw, ch = cropped.size
            buf = io.BytesIO()
            cropped.save(buf, format="PNG")
            
            start_time = time.time()
            verify_res = await client.post(
                f"{base_url}/verify",
                files={"file": (f"test.png", buf.getvalue(), "image/png")},
                timeout=120.0
            )
            elapsed = time.time() - start_time
            
            if verify_res.status_code != 200:
                print(f"{name:<20} | {cw}x{ch:<6} | Error: {verify_res.status_code}")
                continue
                
            data = verify_res.json()
            verdict = data.get("verification_verdict") or data.get("verdict", str(data))
            provenance = data.get("provenance")
            
            uuid_rec = "Yes" if provenance else "No"
            # Hash match can be inferred from TRACED_BUT_MODIFIED vs AUTHENTIC_UNMODIFIED
            if verdict == "AUTHENTIC_UNMODIFIED":
                hash_match = "Yes"
            elif verdict == "TRACED_BUT_MODIFIED":
                hash_match = "No"
            else:
                hash_match = "N/A"
            
            print(f"{name:<20} | {cw}x{ch:<6} | {str(verdict):<25} | {uuid_rec:<6} | {hash_match:<6} | {elapsed:.2f}s")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_crop_robustness.py <path_to_image>")
        sys.exit(1)
    asyncio.run(run_tests(sys.argv[1]))
