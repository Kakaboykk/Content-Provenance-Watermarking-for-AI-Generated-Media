import asyncio
import httpx
from app.core.config import settings

async def main():
    url = (
        "https://router.huggingface.co/hf-inference/models/"
        + settings.AI_DETECTOR_MODEL
    )

    with open("test.jpg", "rb") as f:
        image = f.read()

    headers = {
        "Authorization": f"Bearer {settings.AI_API_KEY}",
        "Content-Type": "image/jpeg",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            url,
            headers=headers,
            content=image,
        )

    print("Status:", response.status_code)
    print("Response:", response.text)

asyncio.run(main())