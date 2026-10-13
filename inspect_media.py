from PIL import Image

files = [
    "media_1791481304385.png",
    "media_1791481397380.png",
    "media_1791489456223.png"
]

base_dir = "C:\\Users\\priti\\.gemini\\antigravity-ide\\brain\\184bccdd-b78f-4283-aaaa-9aed5aaade9a\\.user_uploaded\\"

for f in files:
    try:
        img = Image.open(base_dir + f)
        print(f"{f}: format={img.format}, mode={img.mode}, size={img.size}")
    except Exception as e:
        print(f"Error reading {f}: {e}")
