from PIL import Image, ImageChops
import numpy as np

def test():
    img_rgba = Image.open(r"C:\Users\priti\Downloads\gen image\beachside protected 15.png")
    
    img_rgb_direct = img_rgba.convert("RGB")
    
    background = Image.new('RGBA', img_rgba.size, (255, 255, 255))
    img_composited = Image.alpha_composite(background, img_rgba).convert('RGB')
    
    diff = ImageChops.difference(img_rgb_direct, img_composited)
    print(f"Difference extrema: {diff.getextrema()}")
    
    arr1 = np.array(img_rgb_direct)
    arr2 = np.array(img_composited)
    
    print(f"Max absolute diff: {np.max(np.abs(arr1.astype(int) - arr2.astype(int)))}")

if __name__ == "__main__":
    test()
