import reedsolo
from typing import List
from watermark.config import RS_NSYM

class ECCError(Exception):
    pass

def rs_encode(payload_bytes: bytes) -> bytes:
    """
    Encode payload bytes using Reed-Solomon RS(48,24).
    Input: 24 bytes
    Output: 48 bytes
    """
    rs = reedsolo.RSCodec(nsym=RS_NSYM)
    encoded = rs.encode(payload_bytes)
    return bytes(encoded)

def rs_decode(encoded_bytes: bytes) -> bytes:
    """
    Decode received bytes using Reed-Solomon RS(48,24).
    Input: up to 48 bytes
    Output: 24 decoded bytes
    Raises ECCError if decoding fails.
    """
    rs = reedsolo.RSCodec(nsym=RS_NSYM)
    try:
        decoded_msg, _, _ = rs.decode(encoded_bytes)
        return bytes(decoded_msg)
    except reedsolo.ReedSolomonError as e:
        raise ECCError("RS decoding failed") from e
