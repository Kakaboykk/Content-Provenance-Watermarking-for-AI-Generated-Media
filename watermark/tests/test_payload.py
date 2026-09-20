import pytest
import uuid
from watermark.payload import (
    create_payload_bytes, serialize_payload_to_bits, 
    deserialize_bits_to_bytes, parse_payload_bytes
)

def test_payload_roundtrip():
    uid = uuid.uuid4()
    payload = create_payload_bytes(uid)
    bits = serialize_payload_to_bits(payload)
    deserialized = deserialize_bits_to_bytes(bits)
    parsed_uid = parse_payload_bytes(deserialized)
    
    assert payload == deserialized
    assert uid == parsed_uid
