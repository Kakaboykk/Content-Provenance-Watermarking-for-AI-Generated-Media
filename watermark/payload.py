import uuid
import binascii
from typing import List

from watermark.config import WATERMARK_MAGIC, PAYLOAD_BYTES

class PayloadError(Exception):
    pass

def create_payload_bytes(provenance_id: uuid.UUID) -> bytes:
    """
    Construct the 24-byte payload:
    Bytes 0-3: Magic (4 bytes)
    Bytes 4-19: UUID (16 bytes)
    Bytes 20-23: CRC-32 (4 bytes, computed over bytes 0-19)
    """
    magic_bytes = WATERMARK_MAGIC.to_bytes(4, byteorder='big')
    uuid_bytes = provenance_id.bytes
    
    # Payload before CRC is 20 bytes
    payload_head = magic_bytes + uuid_bytes
    
    # Compute CRC-32
    crc = binascii.crc32(payload_head) & 0xFFFFFFFF
    crc_bytes = crc.to_bytes(4, byteorder='big')
    
    full_payload = payload_head + crc_bytes
    return full_payload

def serialize_payload_to_bits(payload_bytes: bytes) -> List[int]:
    """
    Serialize bytes to a flat list of bits (MSB first).
    """
    bits = []
    for b in payload_bytes:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits

def deserialize_bits_to_bytes(bits: List[int]) -> bytes:
    """
    Deserialize a flat list of bits back to bytes (MSB first).
    """
    if len(bits) % 8 != 0:
        raise ValueError("Bit length must be a multiple of 8.")
    
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits[i+j]
        byte_array.append(byte_val)
    return bytes(byte_array)

def parse_payload_bytes(payload_bytes: bytes) -> uuid.UUID:
    """
    Parse the 24-byte payload and validate magic and CRC.
    Returns the UUID if valid.
    Raises PayloadError if invalid.
    """
    if len(payload_bytes) != PAYLOAD_BYTES:
        raise PayloadError(f"Invalid payload length: {len(payload_bytes)} != {PAYLOAD_BYTES}")
        
    # Extract parts
    magic_bytes = payload_bytes[0:4]
    uuid_bytes = payload_bytes[4:20]
    stored_crc_bytes = payload_bytes[20:24]
    
    # Validate magic
    magic_val = int.from_bytes(magic_bytes, byteorder='big')
    if magic_val != WATERMARK_MAGIC:
        raise PayloadError(f"Magic mismatch: 0x{magic_val:08X} != 0x{WATERMARK_MAGIC:08X}")
        
    # Validate CRC
    computed_crc = binascii.crc32(payload_bytes[:20]) & 0xFFFFFFFF
    stored_crc = int.from_bytes(stored_crc_bytes, byteorder='big')
    if computed_crc != stored_crc:
        raise PayloadError(f"CRC mismatch: {computed_crc:08X} != {stored_crc:08X}")
        
    return uuid.UUID(bytes=uuid_bytes)
