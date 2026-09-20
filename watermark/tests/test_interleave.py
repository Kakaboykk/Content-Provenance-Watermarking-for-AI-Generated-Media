import pytest
import random
from watermark.interleave import interleave, deinterleave

def test_interleave_roundtrip():
    bits = [random.randint(0, 1) for _ in range(384)]
    interleaved = interleave(bits)
    assert len(interleaved) == 384
    assert interleaved != bits # With high probability
    
    deinterleaved = deinterleave(interleaved)
    assert bits == deinterleaved
