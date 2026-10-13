from PIL import Image

def analyze_profile():
    file_path = r"C:\Users\priti\Downloads\gen image\beachside protected 15.png"
    img = Image.open(file_path)
    
    print("UI File Info:")
    print("Info dict:", img.info)
    if 'icc_profile' in img.info:
        print("ICC Profile present!")
    else:
        print("No ICC Profile")

if __name__ == "__main__":
    analyze_profile()
