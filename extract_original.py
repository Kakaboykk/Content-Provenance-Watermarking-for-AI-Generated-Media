import time
from PIL import Image
import io

from watermark.extract import extract_watermark_full

def analyze():
    file_path = r"C:\Users\priti\Downloads\gen image\beachside protected.png"
    img = Image.open(file_path).convert("RGB")
    verdict, uid, stats = extract_watermark_full(img)
    print(f"Original Status: {verdict}")
    print(f"Original UUID: {uid}")
    print(f"Original Stats: {stats}")

if __name__ == "__main__":
    analyze()
