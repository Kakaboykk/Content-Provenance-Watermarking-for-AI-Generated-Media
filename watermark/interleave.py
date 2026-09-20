from typing import List

def interleave(bits: List[int]) -> List[int]:
    """
    Column-major interleave of 384 bits (48 bytes x 8 bits/byte).
    """
    if len(bits) != 384:
        raise ValueError(f"Expected 384 bits for interleaving, got {len(bits)}")
        
    result = []
    for col in range(8):        # bit position within each RS symbol
        for row in range(48):   # RS symbol index
            result.append(bits[row * 8 + col])
    return result

def deinterleave(bits: List[int]) -> List[int]:
    """
    Reverse the column-major interleaving of 384 bits.
    """
    if len(bits) != 384:
        raise ValueError(f"Expected 384 bits for deinterleaving, got {len(bits)}")
        
    result = [0] * 384
    for col in range(8):        # bit position within each RS symbol
        for row in range(48):   # RS symbol index
            result[row * 8 + col] = bits[col * 48 + row]
    return result
