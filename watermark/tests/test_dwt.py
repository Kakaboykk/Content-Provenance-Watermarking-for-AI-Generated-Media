import pytest
import numpy as np
from watermark.dwt import apply_dwt, apply_idwt

def test_dwt_roundtrip():
    # Create random 512x512 array
    np.random.seed(42)
    Y = np.random.rand(512, 512).astype(np.float32) * 255.0
    
    coeffs = apply_dwt(Y)
    Y_reconstructed = apply_idwt(coeffs)
    
    # Check if close
    np.testing.assert_allclose(Y, Y_reconstructed, rtol=1e-4, atol=1e-4)
