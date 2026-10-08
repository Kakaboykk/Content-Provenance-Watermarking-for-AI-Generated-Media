import asyncio
import io
import time
import httpx
from PIL import Image

async def test_odd_offset_crop():
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        with open(path, "rb") as f:
            original_bytes = f.read()
            
        embed_res = await client.post(
            "http://127.0.0.1:8000/watermark/embed",
            files={"file": ("original.jpg", original_bytes, "image/jpeg")}
        )
        protected_img = Image.open(io.BytesIO(embed_res.content))
        w, h = protected_img.size
        
        # Crop 25 pixels from left, 1 from right. Total width = 512 - 26 = 486. dx_max = 26
        c1 = protected_img.crop((25, 0, w - 1, h))
        b1 = io.BytesIO()
        c1.save(b1, format="PNG")
        
        t0 = time.time()
        res1 = await client.post(
            "http://127.0.0.1:8000/verify",
            files={"file": ("test.png", b1.getvalue(), "image/png")}
        )
        print(f"Crop L:25 R:1 Verify took {time.time() - t0:.2f}s, verdict: {res1.json().get('verdict')}")
        
if __name__ == "__main__":
    asyncio.run(test_odd_offset_crop())
