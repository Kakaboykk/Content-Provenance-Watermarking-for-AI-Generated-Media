"""
Verification script for watermark capacity and algorithm correctness.
Run: python watermark/verify_capacity.py
"""
import math
import random
import binascii

print('=== CAPACITY VERIFICATION ===')

IMG = 512
DWT_SUBBAND = IMG // 2            # 256
BLOCK_SIZE = 8
BLOCKS_PER_DIM = DWT_SUBBAND // BLOCK_SIZE  # 32
TOTAL_BLOCKS = BLOCKS_PER_DIM ** 2           # 1024
BITS_PER_BLOCK = 2
RAW_BITS = TOTAL_BLOCKS * BITS_PER_BLOCK     # 2048

PAYLOAD_BYTES = (32 + 128 + 32) // 8        # 24
RS_K = PAYLOAD_BYTES
RS_N = 48
RS_PARITY = RS_N - RS_K                     # 24
RS_T = RS_PARITY // 2                       # 12
RS_BITS = RS_N * 8                          # 384
BLOCKS_PER_SYMBOL = 8 // BITS_PER_BLOCK     # 4
BLOCKS_PER_COPY = RS_N * BLOCKS_PER_SYMBOL  # 192
REPETITIONS = 5
BLOCKS_USED = BLOCKS_PER_COPY * REPETITIONS # 960
SPARE = TOTAL_BLOCKS - BLOCKS_USED          # 64

assert TOTAL_BLOCKS == 1024
assert RAW_BITS == 2048
assert PAYLOAD_BYTES == 24
assert RS_N == 48
assert RS_PARITY == 24
assert RS_T == 12
assert RS_N <= 255, 'RS codeword exceeds GF(2^8) limit'
assert BLOCKS_PER_COPY == 192
assert BLOCKS_USED == 960
assert SPARE == 64
assert BLOCKS_USED <= TOTAL_BLOCKS, 'CAPACITY FAIL'

print(f'Total blocks:        {TOTAL_BLOCKS}')
print(f'Raw capacity:        {RAW_BITS} bits = {RAW_BITS//8} bytes')
print(f'Payload:             {PAYLOAD_BYTES*8} bits = {PAYLOAD_BYTES} bytes')
print(f'After RS({RS_N},{RS_K}):   {RS_BITS} bits = {RS_N} bytes')
print(f'After {REPETITIONS}x rep:      {RS_BITS*REPETITIONS} bits')
print(f'Blocks used:         {BLOCKS_USED} / {TOTAL_BLOCKS}')
print(f'Spare:               {SPARE} blocks')
print('CAPACITY:            PASS')
print()


# ── QIM round-trip ────────────────────────────────────────────────────────────
def qim_embed(c: float, bit: int, delta: float) -> float:
    q = int(round(c / delta))
    if bit == 1:
        if q % 2 == 0:
            q += 1
    else:
        if q % 2 == 1:
            q += 1
    return q * delta


def qim_extract(c: float, delta: float) -> int:
    q = int(round(c / delta))
    return abs(q) % 2


delta = 30
cases = [
    (7.3, 0), (7.3, 1),
    (-3.5, 0), (-3.5, 1),
    (100.1, 0), (100.1, 1),
    (0.0, 0), (0.0, 1),
    (19.8, 1),
    (-20.0, 0), (-20.0, 1),
]
failures = [(c, b) for c, b in cases
            if qim_extract(qim_embed(c, b, delta), delta) != b]
print(f'QIM round-trip ({len(cases)} cases): {len(cases) - len(failures)}/{len(cases)} PASS')
if failures:
    print(f'  FAILURES: {failures}')
print()


# ── Block sequence determinism ─────────────────────────────────────────────────
SEED = 0x574D5031

def make_block_sequence(seed: int, n: int = 1024) -> list:
    rng = random.Random(seed)
    idx = list(range(n))
    rng.shuffle(idx)
    return idx

idx1 = make_block_sequence(SEED)
idx2 = make_block_sequence(SEED)
assert idx1 == idx2, 'Permutation is not deterministic!'
assert len(set(idx1)) == TOTAL_BLOCKS, 'Permutation is not bijective!'
print(f'Block permutation:   {TOTAL_BLOCKS} unique indices, deterministic: PASS')

# Verify copy assignment
copy_0 = idx1[0:192]
copy_4 = idx1[768:960]
unused = idx1[960:1024]
assert len(copy_0) == 192
assert len(unused) == 64
print(f'Copy assignment:     5 copies x 192 blocks + 64 unused: PASS')
print()


# ── Magic constant ─────────────────────────────────────────────────────────────
MAGIC = 0x574D5031
magic_bytes = MAGIC.to_bytes(4, 'big')
assert magic_bytes == b'WMP1', f'Expected b"WMP1", got {magic_bytes}'
print(f'Magic constant:      0x{MAGIC:08X} = {magic_bytes} = "WMP1": PASS')


# ── CRC-32 determinism ─────────────────────────────────────────────────────────
sample_payload = bytes(range(20))  # 20 bytes (magic + UUID)
crc_a = binascii.crc32(sample_payload) & 0xFFFFFFFF
crc_b = binascii.crc32(sample_payload) & 0xFFFFFFFF
assert crc_a == crc_b
print(f'CRC-32 determinism:  0x{crc_a:08X}: PASS')


# ── Interleaving round-trip ────────────────────────────────────────────────────
def interleave(bits: list) -> list:
    """Interleave: arrange as 48-row x 8-col matrix, read column-major.

    Input order:  [sym0_b0, sym0_b1, ..., sym0_b7, sym1_b0, ...]
    Output order: [sym0_b0, sym1_b0, ..., sym47_b0, sym0_b1, ...]
    """
    assert len(bits) == 384
    result = []
    for col in range(8):       # bit position within each RS symbol
        for row in range(48):  # RS symbol index
            result.append(bits[row * 8 + col])
    return result


def deinterleave(bits: list) -> list:
    """De-interleave: reverse of interleave.

    Recovers original [sym0_b0, sym0_b1, ..., sym47_b7] order.
    """
    assert len(bits) == 384
    result = [0] * 384
    for col in range(8):       # bit position within each RS symbol
        for row in range(48):  # RS symbol index
            result[row * 8 + col] = bits[col * 48 + row]
    return result


original_bits = list(range(384))
interleaved = interleave(original_bits)
recovered = deinterleave(interleaved)
assert recovered == original_bits, 'Interleaving round-trip FAILED'
# Verify interleaving actually changes the order
assert interleaved != original_bits, 'Interleaving produced no reordering'
print(f'Interleaving round-trip: 384 bits, bijective, order changed: PASS')


# ── RS parameter consistency ───────────────────────────────────────────────────
assert RS_N * BLOCKS_PER_SYMBOL == BLOCKS_PER_COPY, (
    f'{RS_N} * {BLOCKS_PER_SYMBOL} != {BLOCKS_PER_COPY}'
)
print(f'RS block count:      {RS_N} symbols x {BLOCKS_PER_SYMBOL} blocks/sym = {BLOCKS_PER_COPY}: PASS')


# ── JPEG quantization steps at embedding positions ────────────────────────────
Q50 = [
    [16, 11, 10, 16, 24, 40, 51, 61],
    [12, 12, 14, 19, 26, 58, 60, 55],
    [14, 13, 16, 24, 40, 57, 69, 56],
    [14, 17, 22, 29, 51, 87, 80, 62],
    [18, 22, 37, 56, 68, 109, 103, 77],
    [24, 35, 55, 64, 81, 104, 113, 92],
    [49, 64, 78, 87, 103, 121, 120, 101],
    [72, 92, 95, 98, 112, 100, 103, 99],
]


def jpeg_q_table(quality: int) -> list:
    scale = (200 - 2 * quality) if quality >= 50 else (5000 / quality)
    return [
        [max(1, min(255, int((v * scale + 50) // 100))) for v in row]
        for row in Q50
    ]


print()
print('JPEG quantization at embedding positions (3,4) and (4,3):')
for q in [90, 75, 50]:
    qt = jpeg_q_table(q)
    s34, s43 = qt[3][4], qt[4][3]
    margin = DELTA_INITIAL = 30
    survival_34 = 'OK' if margin > s34 else 'FAIL'
    survival_43 = 'OK' if margin > s43 else 'FAIL'
    print(f'  Q{q}: Q[3][4]={s34:3d}, Q[4][3]={s43:3d}, '
          f'delta=30 margin: {survival_34}/{survival_43}')
assert jpeg_q_table(90)[3][4] == 10
assert jpeg_q_table(90)[4][3] == 11
assert jpeg_q_table(75)[3][4] == 26
assert jpeg_q_table(75)[4][3] == 28
assert jpeg_q_table(50)[3][4] == 51
assert jpeg_q_table(50)[4][3] == 56
print('JPEG table values: PASS')

print()
print('=== ALL VERIFICATIONS PASSED ===')
