from PIL import Image

def analyze():
    file_path = r"C:\Users\priti\Downloads\multimedia project\watermarked_synthetic.png"
    img = Image.open(file_path)
    print(f"Synthetic File Properties:")
    print(f"Format: {img.format}")
    print(f"Mode: {img.mode}")
    print(f"Size: {img.size}")

if __name__ == "__main__":
    analyze()
