import pytest
from watermark.embed import qim_embed

def test_qim_embed():
    c = 100.0
    delta = 30.0
    
    # Embed 0 -> must round to even multiple of delta
    c_0 = qim_embed(c, 0, delta)
    assert (c_0 / delta) % 2 == 0
    
    # Embed 1 -> must round to odd multiple of delta
    c_1 = qim_embed(c, 1, delta)
    assert (c_1 / delta) % 2 == 1
