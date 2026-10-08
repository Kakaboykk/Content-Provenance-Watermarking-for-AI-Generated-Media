import asyncio
import io
import httpx
from PIL import Image

async def test_ui_upload():
    # 1. Load an image
    path = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\media_1791481304385.png"
    
    # 2. Embed
    async with httpx.AsyncClient(timeout=60.0) as client:
        with open(path, "rb") as f:
            original_bytes = f.read()
            
        embed_res = await client.post(
            "http://127.0.0.1:8000/watermark/embed",
            files={"file": ("original.jpg", original_bytes, "image/jpeg")}
        )
        if embed_res.status_code != 200:
            print("Embed failed:", embed_res.text)
            return
            
        protected_img = Image.open(io.BytesIO(embed_res.content))
        
        # 3. Crop 5% from left (meaning crop off the left side)
        w, h = protected_img.size
        crop_w = int(w * 0.95)
        # crop off left means we keep the right part
        cropped = protected_img.crop((w - crop_w, 0, w, h))
        
        buf = io.BytesIO()
        cropped.save(buf, format="PNG")
        
        # 4. Verify
        print(f"Uploading cropped {cropped.size} to /verify")
        verify_res = await client.post(
            "http://127.0.0.1:8000/verify",
            files={"file": ("test.png", buf.getvalue(), "image/png")}
        )
        
        print("Status:", verify_res.status_code)
        print("Response:", verify_res.json())

if __name__ == "__main__":
    asyncio.run(test_ui_upload())
