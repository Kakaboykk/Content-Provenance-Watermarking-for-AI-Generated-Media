import httpx
import asyncio
import io
from PIL import Image

async def run_tests():
    base_url = "http://127.0.0.1:8000"
    
    print("[1] Generating baseline image")
    async with httpx.AsyncClient(timeout=60.0) as client:
        gen_res = await client.post(f"{base_url}/generate", json={"prompt": "A peaceful landscape"})
        original_img_bytes = gen_res.content
        
        embed_res = await client.post(
            f"{base_url}/watermark/embed",
            files={"file": ("original.jpg", original_img_bytes, "image/jpeg")}
        )
        protected_img = Image.open(io.BytesIO(embed_res.content))
        
        print("Done.")

if __name__ == "__main__":
    asyncio.run(run_tests())
