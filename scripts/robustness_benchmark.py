import os
import uuid
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO

from watermark.embed import embed_watermark
from watermark.extract import extract_watermark_with_stats
from watermark.metrics import evaluate_image_quality
from watermark.payload import create_payload_bytes
from watermark.config import DELTA_INITIAL
from watermark.ecc import rs_encode
from watermark.ecc import rs_encode

# Deterministic UUID for reproducibility
PROVENANCE_ID = uuid.UUID('12345678-1234-5678-1234-567812345678')
EXPECTED_PAYLOAD_BYTES = rs_encode(create_payload_bytes(PROVENANCE_ID))

def calculate_ber(candidate_bytes: bytes, expected_bytes: bytes) -> float:
    if candidate_bytes is None or len(candidate_bytes) != len(expected_bytes):
        return 1.0 # 100% error
    errors = 0
    total_bits = len(expected_bytes) * 8
    for c_byte, e_byte in zip(candidate_bytes, expected_bytes):
        diff = c_byte ^ e_byte
        errors += bin(diff).count("1")
    return errors / total_bits

def generate_test_images():
    images = {}
    np.random.seed(42)
    
    # 1. Natural scene proxy (gradient + smooth noise)
    img_natural = np.zeros((512, 512, 3), dtype=np.uint8)
    for y in range(512):
        for x in range(512):
            img_natural[y, x, 0] = (x + y) % 256
            img_natural[y, x, 1] = (x * 2) % 256
            img_natural[y, x, 2] = 100
    noise = np.random.normal(0, 10, (512, 512, 3))
    images["Natural (Synthetic Proxy)"] = Image.fromarray(np.clip(img_natural + noise, 0, 255).astype(np.uint8))
    
    # 2. Portrait proxy (center shape, blurred edges)
    img_portrait = np.full((512, 512, 3), 200, dtype=np.uint8)
    y, x = np.ogrid[:512, :512]
    mask = (x - 256)**2 + (y - 256)**2 <= 150**2
    img_portrait[mask] = [150, 100, 80]
    images["Portrait (Synthetic Proxy)"] = Image.fromarray(img_portrait).filter(ImageFilter.GaussianBlur(10))
    
    # 3. Texture-heavy proxy (high frequency noise)
    img_texture = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    images["Texture-heavy (Synthetic Proxy)"] = Image.fromarray(img_texture)
    
    # 4. Low-texture proxy (flat colors with very slow gradients)
    img_flat = np.zeros((512, 512, 3), dtype=np.uint8)
    for y in range(512):
        img_flat[y, :, :] = [int(100 + y/5)] * 3
    images["Low-texture (Synthetic Proxy)"] = Image.fromarray(img_flat)
    
    # 5. Synthetic/generated proxy (geometric patterns)
    img_gen = np.zeros((512, 512, 3), dtype=np.uint8)
    for i in range(0, 512, 32):
        img_gen[i:i+16, :] = [200, 50, 50]
        img_gen[:, i:i+16] = [50, 200, 50]
    images["Generated (Synthetic Proxy)"] = Image.fromarray(img_gen)
    
    return images

def transform_baseline(img):
    return img

def transform_jpeg_90(img):
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return Image.open(buf)

def transform_jpeg_75(img):
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=75)
    buf.seek(0)
    return Image.open(buf)

def transform_jpeg_50(img):
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=50)
    buf.seek(0)
    return Image.open(buf)

def transform_resize_50(img):
    return img.resize((256, 256), Image.Resampling.LANCZOS)

def transform_resize_75(img):
    return img.resize((384, 384), Image.Resampling.LANCZOS)

def transform_resize_150(img):
    return img.resize((768, 768), Image.Resampling.LANCZOS)

def transform_brightness_up(img):
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(1.2)

def transform_brightness_down(img):
    enhancer = ImageEnhance.Brightness(img)
    return enhancer.enhance(0.8)

def transform_noise(img):
    arr = np.array(img).astype(np.float32)
    noise = np.random.normal(0, 5, arr.shape)
    return Image.fromarray(np.clip(arr + noise, 0, 255).astype(np.uint8))

def transform_crop_10(img):
    # 10% edge crop (keep center 90%)
    w, h = img.size
    crop_w, crop_h = int(w * 0.1), int(h * 0.1)
    return img.crop((crop_w//2, crop_h//2, w - crop_w//2, h - crop_h//2))

def transform_crop_25(img):
    # 25% edge crop (keep center 75%)
    w, h = img.size
    crop_w, crop_h = int(w * 0.25), int(h * 0.25)
    return img.crop((crop_w//2, crop_h//2, w - crop_w//2, h - crop_h//2))

TRANSFORMATIONS = {
    "Baseline": transform_baseline,
    "JPEG Q90": transform_jpeg_90,
    "JPEG Q75": transform_jpeg_75,
    "JPEG Q50 (Experimental)": transform_jpeg_50,
    "Resize 50%": transform_resize_50,
    "Resize 75%": transform_resize_75,
    "Resize 150%": transform_resize_150,
    "Brightness +20%": transform_brightness_up,
    "Brightness -20%": transform_brightness_down,
    "Gaussian Noise (sigma=5)": transform_noise,
    "Crop 10% (Experimental)": transform_crop_10,
    "Crop 25% (Experimental)": transform_crop_25,
}

def evaluate_transformation(name, transform_fn, images, delta):
    results = []
    
    for img_name, img in images.items():
        # Embed
        wm_img = embed_watermark(img, PROVENANCE_ID, delta=delta)
        
        # Save to disk first (lossless)
        tmp_path = f"tmp_{name.replace(' ', '_').replace('%', '')}.png"
        wm_img.save(tmp_path, "PNG")
        
        # Transform
        saved_img = Image.open(tmp_path)
        transformed_img = transform_fn(saved_img)
        
        # We need to save the transformed image and reload if it's resize/crop
        # because extraction pipeline preprocess_image expects PIL image, but
        # to strictly follow pipeline "Original -> watermark -> save -> transform -> reload -> extract"
        trans_path = f"tmp_trans_{name.replace(' ', '_').replace('%', '')}.png"
        transformed_img.save(trans_path, "PNG")
        reloaded_img = Image.open(trans_path)
        
        # Metrics before extraction
        # For resize/crop, we need to compare against the original of the SAME SIZE if we want exact PSNR/SSIM,
        # but the spec says "For every test image calculate PSNR SSIM". It usually implies PSNR on the canonical size.
        # `evaluate_image_quality` automatically preprocesses both to 512x512, which handles resize nicely.
        # Wait, PSNR should be computed between the WATERMARKED PNG and ORIGINAL PNG. 
        # The prompt says: "Record ... PSNR, SSIM" for each transformation. 
        # Does it mean PSNR of the transformed image vs original? Yes, likely.
        psnr, ssim = evaluate_image_quality(img, reloaded_img)
        
        # Extract
        verdict, extracted_id, stats = extract_watermark_with_stats(reloaded_img, delta=delta)
        
        ber = calculate_ber(stats["candidate_bytes"], EXPECTED_PAYLOAD_BYTES)
        
        success = (verdict == "AUTHENTIC_UNMODIFIED" or verdict == "TRACED_BUT_MODIFIED") and extracted_id == PROVENANCE_ID
        
        results.append({
            "image": img_name,
            "success": success,
            "ber": ber,
            "ecc_success": stats["ecc_success"],
            "crc_success": stats["crc_success"],
            "uuid_match": extracted_id == PROVENANCE_ID,
            "psnr": psnr,
            "ssim": ssim
        })
        
        # Cleanup
        os.remove(tmp_path)
        os.remove(trans_path)
        
    return results

def aggregate_results(results):
    total = len(results)
    successes = sum(1 for r in results if r["success"])
    bers = [r["ber"] for r in results]
    psnrs = [r["psnr"] for r in results]
    ssims = [r["ssim"] for r in results]
    
    return {
        "total": total,
        "successes": successes,
        "success_rate": (successes / total) * 100,
        "mean_ber": np.mean(bers),
        "max_ber": np.max(bers),
        "mean_psnr": np.mean(psnrs),
        "min_psnr": np.min(psnrs),
        "mean_ssim": np.mean(ssims),
        "min_ssim": np.min(ssims)
    }

def main():
    print("Generating synthetic test images...")
    images = generate_test_images()
    
    os.makedirs("docs", exist_ok=True)
    
    report_lines = [
        "# Phase 1: Robustness Benchmark Report",
        "",
        "Baseline Configuration: `DELTA = 30`",
        "",
        "## Test Images (Synthetic Proxies)",
        "1. Natural scene",
        "2. Portrait",
        "3. Texture-heavy",
        "4. Low-texture",
        "5. Synthetic/generated",
        "",
        "## Transformation Results",
        ""
    ]
    
    print("Running baseline transformations...")
    for t_name, t_fn in TRANSFORMATIONS.items():
        print(f"Testing {t_name}...")
        results = evaluate_transformation(t_name, t_fn, images, delta=DELTA_INITIAL)
        agg = aggregate_results(results)
        
        report_lines.extend([
            f"### {t_name}",
            f"- **Successful extractions**: {agg['successes']}/{agg['total']}",
            f"- **Success rate**: {agg['success_rate']:.1f}%",
            f"- **Mean BER (before ECC)**: {agg['mean_ber']:.4f}",
            f"- **Max BER**: {agg['max_ber']:.4f}",
            f"- **Mean PSNR**: {agg['mean_psnr']:.2f} dB",
            f"- **Min PSNR**: {agg['min_psnr']:.2f} dB",
            f"- **Mean SSIM**: {agg['mean_ssim']:.4f}",
            f"- **Min SSIM**: {agg['min_ssim']:.4f}",
            ""
        ])
        
    with open("docs/PHASE1_ROBUSTNESS_REPORT.md", "w") as f:
        f.write("\n".join(report_lines))
        
    print("Benchmark complete. Report written to docs/PHASE1_ROBUSTNESS_REPORT.md")

if __name__ == "__main__":
    main()
