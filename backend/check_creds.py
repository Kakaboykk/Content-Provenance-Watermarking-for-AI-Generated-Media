import asyncio
import httpx
from app.core.config import settings

async def main():
    base_url = "https://api.sightengine.com/1.0/check.json"
    data = {
        'models': 'genai',
        'api_user': settings.SIGHTENGINE_API_USER,
        'api_secret': settings.SIGHTENGINE_API_SECRET
    }
    with open("test.jpg", "rb") as f:
        files = {'media': ('image.jpg', f.read(), 'application/octet-stream')}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(base_url, data=data, files=files)
        print("Status:", response.status_code)
        print("Response:", response.text)

if __name__ == "__main__":
    asyncio.run(main())
