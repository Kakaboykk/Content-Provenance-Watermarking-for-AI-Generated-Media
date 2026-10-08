import httpx
import asyncio
import io
import sys
from PIL import Image

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
        
        # Keep original image in memory
        protected_img = Image.open(io.BytesIO(protected_img_bytes))
        
        # Target sizes
        sizes = [
            (512, 512),
            (460, 460),
            (410, 410),
            (384, 384),
            (358, 358),
            (320, 320),
            (256, 256)
        ]
        
        print(f"{'Size':<10} | {'Verdict':<25} | {'UUID Recov?':<12} | {'AI Label':<15} | {'AI Conf':<8}")
        print("-" * 80)
        
        for w, h in sizes:
            resized = protected_img.resize((w, h), Image.Resampling.LANCZOS)
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            resized_bytes = buf.getvalue()
            
            verify_res = await client.post(
                f"{base_url}/verify",
                files={"file": (f"test_{w}.png", resized_bytes, "image/png")}
            )
            
            if verify_res.status_code != 200:
                print(f"{w}x{h:<6} | Error: {verify_res.status_code} {verify_res.text}")
                continue
                
            data = verify_res.json()
            
            verdict = data.get("verification_verdict") or data.get("verdict", str(data))
            provenance = data.get("provenance")
            uuid_rec = "Yes" if provenance else "No"
            
            ai_data = data.get("ai_detection", {})
            ai_label = ai_data.get("label", "N/A")
            ai_conf = ai_data.get("confidence", 0.0)
            
            print(f"{w}x{h:<6} | {str(verdict):<25} | {uuid_rec:<12} | {ai_label:<15} | {ai_conf:.2f}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_resize_api.py <path_to_image>")
        sys.exit(1)
    asyncio.run(run_tests(sys.argv[1]))
