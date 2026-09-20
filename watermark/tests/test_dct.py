import pytest
import numpy as np
from watermark.dct import apply_dct, apply_idct

def test_dct_roundtrip():
    np.random.seed(42)
    block = np.random.rand(8, 8).astype(np.float32) * 255.0
    
    dct_block = apply_dct(block)
    reconstructed = apply_idct(dct_block)
    
    np.testing.assert_allclose(block, reconstructed, rtol=1e-5, atol=1e-4)
