import asyncio
import io
import time
import httpx
from PIL import Image

async def test_ui_upload():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(path, "rb") as f:
            original_bytes = f.read()
            
        t0 = time.time()
        print("Embedding...")
        embed_res = await client.post(
            "http://127.0.0.1:8000/watermark/embed",
            files={"file": ("original.jpg", original_bytes, "image/jpeg")}
        )
        print(f"Embed took {time.time() - t0:.2f}s")
        
        protected_img = Image.open(io.BytesIO(embed_res.content))
        w, h = protected_img.size
        
        # Test 1: 486x512 Left Crop (dx=26)
        c1 = protected_img.crop((w - int(w*0.95), 0, w, h))
        b1 = io.BytesIO()
        c1.save(b1, format="PNG")
        
        t0 = time.time()
        res1 = await client.post(
            "http://127.0.0.1:8000/verify",
            files={"file": ("test.png", b1.getvalue(), "image/png")}
        )
        print(f"Left Crop Verify took {time.time() - t0:.2f}s, verdict: {res1.json().get('verdict')}")
        
        # Test 2: 512x486 Top Crop (dy=26)
        c2 = protected_img.crop((0, h - int(h*0.95), w, h))
        b2 = io.BytesIO()
        c2.save(b2, format="PNG")
        
        t0 = time.time()
        res2 = await client.post(
            "http://127.0.0.1:8000/verify",
            files={"file": ("test.png", b2.getvalue(), "image/png")}
        )
        print(f"Top Crop Verify took {time.time() - t0:.2f}s, verdict: {res2.json().get('verdict')}")
        
if __name__ == "__main__":
    asyncio.run(test_ui_upload())
