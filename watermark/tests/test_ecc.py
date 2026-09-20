import pytest
import os
from watermark.ecc import rs_encode, rs_decode, ECCError

def test_ecc_roundtrip():
    data = os.urandom(24)
    encoded = rs_encode(data)
    assert len(encoded) == 48
    decoded = rs_decode(encoded)
    assert data == decoded
    
def test_ecc_correction():
    data = os.urandom(24)
    encoded = bytearray(rs_encode(data))
    
    # Corrupt 12 bytes
    for i in range(12):
        encoded[i] ^= 0xFF
        
    decoded = rs_decode(bytes(encoded))
    assert data == decoded

def test_ecc_failure():
    data = os.urandom(24)
    encoded = bytearray(rs_encode(data))
    
    # Corrupt 13 bytes (beyond T=12 capability)
    for i in range(13):
        encoded[i] ^= 0xFF
        
    with pytest.raises(ECCError):
        rs_decode(bytes(encoded))
