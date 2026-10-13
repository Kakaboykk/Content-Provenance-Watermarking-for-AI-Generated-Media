import time
from PIL import Image
from watermark.extract import extract_watermark_full

def test():
    img = Image.new("RGB", (320, 320), color="green")
    print("Testing 320x320 (Resize Path)...")
    verdict, uid, stats = extract_watermark_full(img)
    print("320x320 Verdict:", verdict)
    
    img = Image.new("RGB", (435, 435), color="blue")
    print("Testing 435x435 (Crop Path)...")
    verdict, uid, stats = extract_watermark_full(img)
    print("435x435 Verdict:", verdict)
    
    img = Image.new("RGB", (600, 600), color="red")
    print("Testing 600x600 (Resize Path)...")
    verdict, uid, stats = extract_watermark_full(img)
    print("600x600 Verdict:", verdict)

if __name__ == "__main__":
    test()
