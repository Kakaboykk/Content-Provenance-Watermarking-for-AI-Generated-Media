import pytest
import uuid
import os
import numpy as np
from PIL import Image
from watermark.embed import embed_watermark
from watermark.extract import extract_watermark

def test_watermark_end_to_end(tmp_path):
    # Create dummy image
    img = Image.fromarray(np.random.randint(0, 255, (800, 600, 3), dtype=np.uint8))
    
    # Embed
    provenance_id = uuid.uuid4()
    watermarked_img = embed_watermark(img, provenance_id)
    
    # Save to disk as PNG (lossless)
    file_path = str(tmp_path / "watermarked.png")
    watermarked_img.save(file_path, "PNG")
    
    # Reload
    reloaded_img = Image.open(file_path)
    
    # Extract
    verdict, extracted_id = extract_watermark(reloaded_img)
    
    assert verdict == "AUTHENTIC_UNMODIFIED"
    assert provenance_id == extracted_id
