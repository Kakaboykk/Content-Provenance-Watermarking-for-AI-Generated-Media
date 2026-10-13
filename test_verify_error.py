import httpx
import io
import asyncio
from PIL import Image

async def test():
    img = Image.new("RGB", (435, 435), color="green")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    
    files = {"file": ("test.png", img_bytes, "image/png")}
    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post("http://localhost:8000/verify", files=files)
        print(r.status_code)
        print(r.text)

if __name__ == "__main__":
    asyncio.run(test())
