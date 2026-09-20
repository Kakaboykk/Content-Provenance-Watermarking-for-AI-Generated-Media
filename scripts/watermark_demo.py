import os
import uuid
import numpy as np
from PIL import Image
from watermark.embed import embed_watermark
from watermark.extract import extract_watermark
from watermark.metrics import evaluate_image_quality

def run_demo():
    print("=== Watermark Engine Phase 0 Demo ===")
    
    # 1. Create a synthetic test image (natural-like)
    print("Generating synthetic test image...")
    # Generate some smooth gradient/noise to simulate an image rather than pure random noise
    img_array = np.zeros((512, 512, 3), dtype=np.uint8)
    for y in range(512):
        for x in range(512):
            img_array[y, x, 0] = (x + y) % 256
            img_array[y, x, 1] = (x * 2) % 256
            img_array[y, x, 2] = (y * 2) % 256
    
    # Add some noise to make it realistic for DCT
    noise = np.random.randint(0, 50, (512, 512, 3), dtype=np.uint8)
    img_array = np.clip(img_array.astype(np.uint16) + noise, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(img_array)
    img.save("original_synthetic.png")
    
    # 2. Embed
    provenance_id = uuid.uuid4()
    print(f"Embedding UUID: {provenance_id}")
    watermarked_img = embed_watermark(img, provenance_id)
    
    watermarked_path = "watermarked_synthetic.png"
    watermarked_img.save(watermarked_path, "PNG")
    print(f"Saved watermarked image to {watermarked_path}")
    
    # 3. Metrics
    print("Calculating quality metrics...")
    psnr, ssim = evaluate_image_quality(img, watermarked_img)
    print(f"PSNR: {psnr:.2f} dB")
    print(f"SSIM: {ssim:.4f}")
    
    # 4. Extract
    print("Reloading image for blind extraction...")
    reloaded_img = Image.open(watermarked_path)
    
    verdict, extracted_id = extract_watermark(reloaded_img)
    print(f"Verdict: {verdict}")
    print(f"Extracted UUID: {extracted_id}")
    
    if verdict == "AUTHENTIC_UNMODIFIED" and provenance_id == extracted_id:
        print("SUCCESS: End-to-end extraction passed!")
    else:
        print("FAILURE: End-to-end extraction failed!")

if __name__ == "__main__":
    run_demo()
