import pytest
from PIL import Image
import numpy as np
from watermark.preprocess import preprocess_image, postprocess_image

def test_preprocess_size():
    # Create random image
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    Y, Cb, Cr = preprocess_image(img)
    assert Y.shape == (512, 512)
    assert Cb.shape == (512, 512)
    assert Cr.shape == (512, 512)

def test_preprocess_deterministic():
    img = Image.new('RGB', (800, 600), color=(73, 109, 137))
    Y1, Cb1, Cr1 = preprocess_image(img)
    Y2, Cb2, Cr2 = preprocess_image(img)
    assert np.array_equal(Y1, Y2)
    assert np.array_equal(Cb1, Cb2)
    assert np.array_equal(Cr1, Cr2)
