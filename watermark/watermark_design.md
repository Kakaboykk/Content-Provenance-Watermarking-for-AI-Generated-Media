# Watermark Design Specification

## Content-Provenance Watermarking for AI-Generated Media

**Document status:** Implementation-ready specification  
**Version:** 1.0  
**Authority:** This document is the single authoritative source of truth for all watermarking parameters. Every implementation module MUST reference this document. No module may independently redefine constants, coefficient positions, or algorithm variants.

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [Image Standard](#2-image-standard)
3. [Discrete Wavelet Transform (DWT)](#3-discrete-wavelet-transform-dwt)
4. [Discrete Cosine Transform (DCT)](#4-discrete-cosine-transform-dct)
5. [Quantization Index Modulation (QIM)](#5-quantization-index-modulation-qim)
6. [Payload Design](#6-payload-design)
7. [Error Correction: Reed-Solomon](#7-error-correction-reed-solomon)
8. [Capacity Proof Summary](#8-capacity-proof-summary)
9. [Block Allocation and Interleaving](#9-block-allocation-and-interleaving)
10. [Embedding Pipeline](#10-embedding-pipeline)
11. [Blind Extraction Pipeline](#11-blind-extraction-pipeline)
12. [Image Quality Acceptance Criteria](#12-image-quality-acceptance-criteria)
13. [Robustness Scope](#13-robustness-scope)
14. [Verification Verdict System](#14-verification-verdict-system)
15. [SHA-256 Integrity Layer](#15-sha-256-integrity-layer)
16. [Report Alignment Notes](#16-report-alignment-notes)
16. [Cryptographic Authenticity Limitation](#16-cryptographic-authenticity-limitation)
17. [Report Alignment Notes](#17-report-alignment-notes)
18. [Implementation Constants Reference](#18-implementation-constants-reference)

---

## 1. Purpose and Scope

### 1.1 What This Document Defines

This document formally specifies the DWT-DCT watermarking system used to embed and extract invisible provenance identifiers in AI-generated images. It defines:

- Image preprocessing pipeline
- Transform domain parameters (DWT + DCT)
- Embedding algorithm (QIM)
- Payload structure (192 bits)
- Error correction (Reed-Solomon RS(48,24))
- Block allocation (pseudorandom with fixed seed)
- Complete embedding and blind extraction pipelines
- Image quality acceptance criteria
- Robustness scope and limitations
- Four-state verification verdict model

### 1.2 What This Document Does Not Cover

This specification covers only the image watermarking core. The following are out of scope for the MVP:

- Video watermarking
- Audio watermarking
- Neural / learned watermarking (e.g., HiDDeN, Stable Signature)
- C2PA metadata standards
- Blockchain provenance
- Browser extensions or mobile applications

### 1.3 Design Philosophy

The watermark system is designed as a **provenance identifier channel**, not an adversarially secure watermark. It is designed to:

- Survive common non-adversarial image transformations (JPEG compression, resizing, moderate brightness/noise adjustments).
- Provide a reliable link from an image to its registered provenance record.
- Be **blind**: extraction does not require the original image.

It is explicitly **not** designed to:

- Resist deliberate watermark removal by a technically sophisticated adversary.
- Prove that an image is fake or has been tampered with.
- Authenticate image content beyond provenance tracing.

---

## 2. Image Standard

### 2.1 Canonical Resolution

```
CANONICAL_WIDTH  = 512
CANONICAL_HEIGHT = 512
```

All watermarking operations (embedding and extraction) are performed on images normalized to exactly 512 x 512 pixels.

### 2.2 Color Space

```
Input format: RGB
Processing format: YCbCr
Watermark domain: Y (luminance) channel only
```

The Y channel is used exclusively. The Cb and Cr channels pass through unmodified.

### 2.3 Preprocessing Function

The same preprocessing function MUST be applied identically during embedding and during extraction. Any deviation in preprocessing between the two operations will produce misaligned DWT block grids, causing extraction failure.

#### Preprocessing Steps (deterministic, order-fixed)

1. **EXIF rotation**: Apply EXIF orientation metadata using `PIL.ImageOps.exif_transpose()`, then strip all EXIF data.
2. **Alpha removal**: Convert RGBA to RGB by compositing over a white background.
3. **Grayscale expansion**: If image is grayscale (L mode), convert to RGB by replication across channels.
4. **Resize**: Resize the image to 512 x 512 using `PIL.Image.LANCZOS` resampling. Aspect ratio is not preserved; the image is stretched to the canonical size.
5. **Color space**: Convert RGB to YCbCr using `PIL` or OpenCV (ITU-R BT.601 coefficients).
6. **Channel extraction**: Extract the Y channel as a float32 NumPy array in range [0.0, 255.0].

#### Why Step 4 Does Not Preserve Aspect Ratio

Content-preserving resize (letterbox padding) would place watermarked content at non-deterministic pixel offsets relative to the DWT block grid. Deterministic stretching is preferred because the preprocessing function is the same at embed and extract time, and the image content is not used for cryptographic purposes — only the embedded payload ID matters.

#### Important Lossless Constraint

After embedding, the watermarked image MUST be saved as **lossless PNG**. The registered SHA-256 hash is computed from the PNG bytes. Any subsequent JPEG export of the watermarked image is considered a "modification" and will result in a `TRACED_BUT_MODIFIED` verdict, not `AUTHENTIC_UNMODIFIED`.

---

## 3. Discrete Wavelet Transform (DWT)

### 3.1 Parameters

```
WAVELET  = "haar"
DWT_LEVEL = 1
```

### 3.2 DWT Output

Applying one-level 2D Haar DWT to the 512 x 512 Y channel produces four subbands, each of size 256 x 256:

```
LL  -- approximation coefficients (low-low)
LH  -- horizontal detail (low-high)
HL  -- vertical detail (high-low)
WatermarkSubband = HL
HH  -- diagonal detail (high-high)
```

### 3.3 Subband Selection

**Primary embedding subband: HL**

Rationale for each subband:

| Subband | Selection | Reason |
|---------|-----------|--------|
| LL | Do NOT use | Carries low-frequency content. Modifications are perceptually visible. |
| LH | Not selected as primary | Alternative mid-frequency region; may be used for future redundancy. |
| HL | **PRIMARY** | Mid-frequency detail. Best perceptibility/robustness tradeoff for JPEG survival. |
| HH | Do NOT use as primary | High-frequency diagonal detail. Most vulnerable to JPEG quantization. |

### 3.4 Implementation Notes

- Use `pywt.dwt2(Y_channel, 'haar')` to decompose.
- Use `pywt.idwt2((LL, (LH, HL_modified, HH)), 'haar')` to reconstruct.
- Work with float32 arrays throughout. Clip to [0, 255] after IDWT before converting back to uint8.

---

## 4. Discrete Cosine Transform (DCT)

### 4.1 Block Size

```
DCT_BLOCK_SIZE = 8
```

The HL subband (256 x 256) is divided into non-overlapping 8 x 8 blocks:

```
Blocks per row    = 256 / 8 = 32
Blocks per column = 256 / 8 = 32
Total blocks      = 32 x 32 = 1024
```

### 4.2 DCT Application

Apply 2D Type-II DCT to each 8 x 8 block independently:

```python
# Pseudocode
block_dct = cv2.dct(block.astype(np.float32))
```

Or equivalently using SciPy:

```python
from scipy.fft import dctn
block_dct = dctn(block, type=2, norm='ortho')
```

**The normalization mode must be consistent between embedding and extraction.** Use `norm='ortho'` (orthonormal) to ensure the coefficient magnitude scale is consistent across images and implementations.

### 4.3 Embedding Coefficient Positions

```
DCT_COEFF_POS_1 = (3, 4)   # row 3, column 4 (zero-indexed)
DCT_COEFF_POS_2 = (4, 3)   # row 4, column 3 (zero-indexed)
```

These are mid-frequency positions in the 8 x 8 DCT block. In the standard JPEG zig-zag scan order, these correspond to approximately positions 19 and 20 (0-indexed from DC = 0).

**These positions MUST be defined as named constants in `watermark/config.py`. No other module may hardcode these values.**

Each block carries **2 bits** of payload:
- Bit embedded at position (3, 4) via QIM
- Bit embedded at position (4, 3) via QIM

#### Rationale for Mid-Frequency Selection

| Coefficient Region | Zig-zag Position | Selection |
|---|---|---|
| DC (0,0) | 0 | Avoid: changes overall block brightness visibly |
| Low-mid (1,0)-(2,2) | 1-8 | Avoid: perceptually sensitive |
| **Mid (3,3)-(5,5)** | **~14-24** | **TARGET: robustness/imperceptibility tradeoff** |
| High (6,0)-(7,7) | 34-63 | Avoid: destroyed by JPEG high-frequency quantization |

### 4.4 IDCT Application

After modifying coefficients in the DCT domain, apply the inverse DCT to reconstruct the block:

```python
block_reconstructed = cv2.idct(block_dct_modified)
```

---

## 5. Quantization Index Modulation (QIM)

### 5.1 Algorithm Definition

QIM is the sole embedding and extraction method used in this system. It does not require the original image during extraction (blind extraction property).

#### 5.1.1 Parameter

```
DELTA = (configurable, see Section 5.3)
```

Delta is the quantization step size. It must be identical during embedding and extraction.

#### 5.1.2 Embedding

To embed bit `b` (0 or 1) into DCT coefficient `c` using quantization step `Delta`:

```
Step 1:  q = round(c / Delta)
Step 2:  if b == 1:
             if q % 2 == 0:
                 q = q + 1    # force odd
         if b == 0:
             if q % 2 == 1:
                 q = q + 1    # force even
Step 3:  c_watermarked = q * Delta
```

The actual modification applied to the coefficient is `(c_watermarked - c)`. Its magnitude depends on the original coefficient value `c`, the step size `Delta`, and the parity adjustment performed in Step 2. When no parity adjustment is needed (Step 2 leaves `q` unchanged), the modification is `|c - round(c / Delta) * Delta|`, which is at most `Delta / 2`. When a parity adjustment is required (Step 2 increments `q` by 1), the modification may be up to `3 * Delta / 2` in the worst case.

> **No fixed maximum bound is claimed for the general case.** Implementations should not assume `|c_watermarked - c| <= Delta`. The actual distortion per coefficient is data-dependent and must be measured experimentally via PSNR and SSIM on representative images.

#### 5.1.3 Extraction

To extract bit `b` from (potentially transformed) coefficient `c_extracted`:

```
Step 1:  q = round(c_extracted / Delta)
Step 2:  b = q % 2    (0 if q is even, 1 if q is odd)
```

Note: `q % 2` in Python for negative `q` may return -1 for odd negative numbers. Use `int(round(c_extracted / Delta)) % 2` with an explicit positive modulo:

```python
def qim_extract(c_extracted: float, delta: float) -> int:
    q = int(round(c_extracted / delta))
    return abs(q) % 2
```

#### 5.1.4 JPEG Robustness: Heuristic Analysis (Not a Proof)

JPEG compression applies its own DCT quantization with step `Q_j` per coefficient. The intuition behind QIM survival is:

- If `Delta >> Q_j`, the JPEG-quantized coefficient is more likely to round to a value that preserves the embedded parity (`q % 2`).
- A larger `Delta` relative to `Q_j` provides a greater margin against JPEG-induced parity flips.

This comparison provides a useful **initial heuristic for selecting Delta**, but it is **not a proof of JPEG robustness**. Actual survival depends on the specific image content, the JPEG codec implementation, the interaction between the DWT-domain embedding and the JPEG-domain quantization applied to the reconstructed spatial image, and the error-correction capability of the RS + repetition layers.

**JPEG quantization steps at the embedding positions** (from the standard JPEG luminance table, for reference only):

| JPEG Quality | Q[3][4] | Q[4][3] | Initial heuristic: need Delta > |
|---|---|---|---|
| Q90 | 10 | 11 | 11 |
| Q75 | 26 | 28 | 28 |
| Q50 | 51 | 56 | 56 (experimental only) |

These values are computed from the standard JPEG luminance quantization table:

```
scale = (200 - 2 * quality)   for quality >= 50
Q_scaled[i][j] = max(1, min(255, (Q50[i][j] * scale + 50) // 100))
```

> **JPEG robustness must be verified by experiment, not claimed from the table above.** The Q-table analysis guides the choice of initial Delta; the actual extraction success rate at each JPEG quality level is measured during Phase 2 robustness experiments and reported as real measurements.

### 5.2 Delta Tradeoff

```
Larger Delta:
  + stronger robustness (survives higher JPEG compression)
  - greater image distortion (lower PSNR and SSIM)

Smaller Delta:
  + lower image distortion (higher PSNR and SSIM)
  - weaker robustness (fragile under compression)
```

### 5.3 Initial Delta and Experimental Range

The initial value for experiments is:

```
DELTA_INITIAL = 30
```

This value is above the JPEG Q90 heuristic threshold (11) and approximately at the JPEG Q75 heuristic threshold (28). It is a reasonable starting point, not a guaranteed optimum. The Reed-Solomon ECC and 5-copy repetition layers are intended to absorb errors that remain after JPEG processing.

The experimental range is:

```
Test: Delta in {20, 25, 30, 35, 40}
```

For each value, measure PSNR, SSIM, and extraction accuracy at each robustness test level. Choose the smallest Delta that satisfies the following **targets** (to be confirmed by actual experiment during Phase 2):

1. **[Target]** PSNR >= 35 dB on all 5 test images — *not yet measured*
2. **[Target]** SSIM >= 0.95 on all 5 test images — *not yet measured*
3. **[Target]** 100% payload extraction from lossless PNG copy — *not yet measured*
4. **[Target]** >= 95% bit accuracy (post-ECC) from JPEG Q90 copy — *not yet measured*
5. **[Target]** Successful payload extraction (post-ECC) from JPEG Q75 copy — *not yet measured*

**Do not hard-code DELTA = 30 as the final value. Measure and confirm experimentally. Do not claim any of the targets above have been achieved until Phase 2 experiments are complete.**

---

## 6. Payload Design

### 6.1 Logical Payload Structure

The logical payload is exactly **192 bits (24 bytes)**:

```
+---------+----------------------------+---------+
|  Magic  |    Provenance UUID         |   CRC   |
| 32 bits |       128 bits             | 32 bits |
+---------+----------------------------+---------+
  Bytes 0-3    Bytes 4-19                Bytes 20-23
```

Total: 32 + 128 + 32 = **192 bits = 24 bytes**

### 6.2 Magic Header

```
WATERMARK_MAGIC = 0x574D5031
```

ASCII interpretation: `W M P 1` (WaterMark Provenance 1)

The magic header serves two purposes:
1. Allows rapid rejection of random images that happen to produce valid-looking payload patterns.
2. Provides 4 bytes of CRC coverage that can detect burst errors in the magic field itself.

### 6.3 Provenance UUID

A 128-bit UUID (UUID version 4) is the provenance identifier embedded in the watermark. This UUID serves as the lookup key into the PostgreSQL provenance registry.

The UUID is generated once at registration time and never changes.

### 6.4 CRC-32 Checksum

```
CRC algorithm: CRC-32 (ISO 3309 / ITU-T V.42)
CRC input:     bytes 0 through 19 (magic + UUID, 20 bytes)
CRC output:    4 bytes, stored at bytes 20-23
```

Python implementation:

```python
import binascii
crc = binascii.crc32(payload_bytes[:20]) & 0xFFFFFFFF
```

The CRC is computed over the magic header and UUID. During extraction, after Reed-Solomon decoding produces the candidate 24-byte payload, the verifier recomputes CRC over bytes 0-19 and compares with bytes 20-23. If the CRC does not match, the payload is rejected (verdict: `NO_WATERMARK_FOUND` or `WATERMARK_UNRECOVERABLE`).

### 6.5 Byte and Bit Order

```
Byte order:     big-endian (network order)
Bit order:      MSB first within each byte
```

**Magic header (4 bytes, big-endian):**
```
byte[0] = 0x57 = 'W'
byte[1] = 0x4D = 'M'
byte[2] = 0x50 = 'P'
byte[3] = 0x31 = '1'
```

**UUID (16 bytes):** Stored in the canonical UUID byte order as returned by Python's `uuid.uuid4().bytes`.

**CRC-32 (4 bytes, big-endian):**
```
byte[20] = (crc >> 24) & 0xFF
byte[21] = (crc >> 16) & 0xFF
byte[22] = (crc >>  8) & 0xFF
byte[23] =  crc        & 0xFF
```

**Bit serialization:** The 192-bit payload is serialized as a flat bit array. Byte `k` contributes bits at positions `8k` through `8k+7`, with bit `8k` being the MSB of byte `k`:

```
bit[0]   = (byte[0] >> 7) & 1
bit[1]   = (byte[0] >> 6) & 1
...
bit[7]   = (byte[0] >> 0) & 1
bit[8]   = (byte[1] >> 7) & 1
...
bit[191] = (byte[23] >> 0) & 1
```

---

## 7. Error Correction: Reed-Solomon

### 7.1 RS Parameters

```
RS_SYMBOL_SIZE  = 8       # bits per symbol (GF(2^8))
RS_K            = 24      # data symbols (= payload bytes)
RS_2T           = 24      # parity symbols
RS_N            = RS_K + RS_2T = 48   # total encoded symbols
RS_T            = RS_2T / 2 = 12     # symbol errors correctable
GF_FIELD        = GF(2^8) with primitive polynomial x^8 + x^4 + x^3 + x^2 + 1
```

RS(48, 24) can correct up to **12 symbol errors** in the decoded codeword (where each symbol is 8 bits = 1 byte).

### 7.2 RS Constraint

GF(2^8) supports codewords of maximum length n = 255. RS_N = 48 <= 255: valid.

### 7.3 Python Implementation

Use the `reedsolo` library (pure Python):

```python
import reedsolo
rs = reedsolo.RSCodec(nsym=24)   # nsym = number of parity symbols

# Encode (input: 24 bytes, output: 48 bytes)
encoded: bytes = bytes(rs.encode(payload_bytes))  # len=48

# Decode (input: up to 48 bytes, possibly corrupted)
decoded_msg, decoded_msgecc, errata_pos = rs.decode(encoded_received)
# decoded_msg: 24 bytes (original payload)
```

### 7.4 Why RS Instead of Repetition Only

Simple N-of-5 majority voting corrects single-bit errors distributed across the 5 copies. However, JPEG quantization introduces **burst errors**: all 4 blocks carrying a particular 8-bit RS symbol may have their 8 bits corrupted together (because they share the same spatial region or JPEG block). A majority vote over 5 copies does not protect against such correlated burst errors; Reed-Solomon does.

The RS(48,24) layer corrects bursts of up to 12 corrupted bytes anywhere in the 48-byte codeword, regardless of error distribution.

### 7.5 Repetition Layer (Applied After RS Encoding)

After RS encoding, the 48-byte (384-bit) codeword is embedded **5 times** in the image.

```
REPETITIONS = 5
```

During extraction, all 5 copies are extracted independently. Each bit position across the 5 copies is decided by **majority vote**:

```
if (sum of 5 extracted bits at position i) >= 3:
    decoded_bit[i] = 1
else:
    decoded_bit[i] = 0
```

This produces one 384-bit candidate codeword, which is then passed to RS decoding. The majority vote pre-filters obvious bit errors before RS operates.

**Rationale for two layers:**

- Repetition corrects random independent bit flips that affect individual blocks.
- Reed-Solomon corrects burst errors that corrupt multiple consecutive bits in the RS codeword.
- Together they provide substantially more robustness than either layer alone.

### 7.6 Interleaving

To prevent JPEG block-level burst errors from corrupting consecutive RS symbols, the encoded bit stream is **interleaved** before mapping to blocks.

Interleaving procedure:

1. Take the 384-bit RS-encoded bit array for one repetition copy. Interpret it as 48 RS symbols x 8 bits per symbol (symbol-major order: bits of symbol 0, then bits of symbol 1, ...).
2. Reorder the bits column-major: emit bit 0 of all 48 symbols, then bit 1 of all 48 symbols, ..., then bit 7 of all 48 symbols.
3. This produces a 384-bit interleaved sequence.

In code:
```python
def interleave(bits):  # len(bits) == 384
    result = []
    for col in range(8):        # bit position within each RS symbol
        for row in range(48):   # RS symbol index
            result.append(bits[row * 8 + col])
    return result
```

Result: a burst of up to 48 consecutive bit errors (affecting one spatial region in the image) will damage at most 1 bit in each of the 48 RS symbols — maximally spread — rather than completely destroying a few RS symbols.

**De-interleaving during extraction reverses this operation exactly:**

```python
def deinterleave(bits):  # len(bits) == 384
    result = [0] * 384
    for col in range(8):        # bit position within each RS symbol
        for row in range(48):   # RS symbol index
            result[row * 8 + col] = bits[col * 48 + row]
    return result
```

---

## 8. Capacity Proof Summary

See `CAPACITY_CALCULATION.md` for the complete mathematical derivation. Summary:

| Parameter | Value |
|---|---|
| Total blocks available | 1024 |
| Bits per block | 2 (coefficients (3,4) and (4,3)) |
| Raw bit capacity | 2048 bits = 256 bytes |
| Payload (logical) | 192 bits = 24 bytes |
| After RS(48,24) encoding | 384 bits = 48 bytes |
| After 5x repetition | 1920 bits |
| Blocks consumed | 960 |
| Spare blocks | 64 |
| Capacity check | **PASS** (960 <= 1024) |

---

## 9. Block Allocation and Interleaving

### 9.1 Block Indexing

The 1024 available 8x8 blocks in the HL subband are indexed 0 through 1023 in row-major order:

```
block_index = row * 32 + col
where row in [0, 31], col in [0, 31]
```

### 9.2 Deterministic Public Block Permutation

A fixed, deterministic permutation of block indices is generated using a seeded shuffle. The seed is the magic constant:

```
BLOCK_SELECT_SEED = 0x574D5031
```

Permutation algorithm: Fisher-Yates (Knuth) shuffle using Python's `random.Random(seed)`:

```python
import random
rng = random.Random(BLOCK_SELECT_SEED)
indices = list(range(1024))
rng.shuffle(indices)
# indices is now a deterministic permutation of [0, 1023]
```

This permutation is **deterministic, fixed, and image-independent**. The verifier reproduces it using the same seed without any knowledge of the original image.

> **Security note:** `random.Random` is a pseudo-random number generator (Mersenne Twister) suitable for deterministic block distribution, but it is **not cryptographically secure**. Because both the seed (0x574D5031) and the algorithm are public, this permutation provides no security against an attacker who knows them. Its purpose is reproducibility and spatial distribution of the embedded bits, not secrecy of embedding locations. A keyed cryptographic permutation (e.g., using AES-CTR or HMAC-derived indices with a secret key) can be considered in future security-focused work.

### 9.3 Block Assignment to Repetition Copies

The 960 selected blocks are divided into 5 groups of 192 blocks:

```
Copy 0: indices[  0 : 192]
Copy 1: indices[192 : 384]
Copy 2: indices[384 : 576]
Copy 3: indices[576 : 768]
Copy 4: indices[768 : 960]

Unused: indices[960 : 1024]  (64 blocks; left unmodified)
```

Within each copy, the mapping from interleaved bit position to block is sequential:

```
Bit position 2k   -> coefficient (3,4) of block copy_blocks[k]
Bit position 2k+1 -> coefficient (4,3) of block copy_blocks[k]
for k in [0, 191]
```

This ensures bits from the same RS symbol are distributed across multiple non-adjacent blocks (due to interleaving in Section 7.6 combined with the pseudorandom permutation).

### 9.4 Synchronization

No synchronization blocks are required. The block sequence is fully deterministic from the fixed seed. The verifier never needs to search for a synchronization marker.

If the image has been resized, the preprocessing step normalizes it back to 512 x 512 before extraction, restoring the block grid to its canonical positions.

---

## 10. Embedding Pipeline

The complete embedding pipeline, step by step:

```
INPUT: RGB image (any size)

Step 1:  Preprocessing
         -> EXIF rotation -> Alpha removal -> Resize to 512x512
         -> RGB to YCbCr -> Extract Y channel (float32, [0,255])

Step 2:  Build payload
         -> magic (4 bytes) + UUID (16 bytes) + CRC-32 (4 bytes)
         -> 24 bytes total
         -> Serialize to 192-bit array (MSB first)

Step 3:  Reed-Solomon encoding
         -> rs = RSCodec(nsym=24)
         -> encoded = rs.encode(payload_bytes)  # 48 bytes

Step 4:  Interleaving
         -> reshape encoded bits to 48x8 matrix
         -> read column-major -> 384-bit interleaved array

Step 5:  Repetition
         -> repeat the 384-bit interleaved array 5 times
         -> total: 1920 bits

Step 6:  Generate block sequence
         -> rng = random.Random(0x574D5031)
         -> indices = list(range(1024)); rng.shuffle(indices)
         -> assign to 5 copies (indices[0:192], ..., indices[768:960])

Step 7:  DWT decomposition
         -> LL, (LH, HL, HH) = pywt.dwt2(Y_channel, 'haar')

Step 8:  For each copy c in [0,4]:
         For each block position k in [0,191]:
             block_idx = copy_blocks[c][k]
             row = block_idx // 32; col = block_idx % 32
             Extract 8x8 block from HL at (row*8, col*8)
             Apply 2D DCT (norm='ortho')
             bit_0 = interleaved_bit[c * 384 + 2*k]
             bit_1 = interleaved_bit[c * 384 + 2*k + 1]
             Modify coefficient (3,4) with bit_0 using QIM(Delta)
             Modify coefficient (4,3) with bit_1 using QIM(Delta)
             Apply IDCT (norm='ortho')
             Write modified block back to HL

Step 9:  DWT reconstruction
         -> Y_watermarked = pywt.idwt2((LL, (LH, HL_modified, HH)), 'haar')
         -> Clip to [0, 255]

Step 10: YCbCr to RGB
         -> Recombine Y_watermarked with original Cb, Cr
         -> Convert back to RGB

Step 11: Save as lossless PNG
         -> Compute SHA-256 of PNG bytes -> registered_hash

OUTPUT: Watermarked PNG image + registered_hash + UUID
```

---

## 11. Blind Extraction Pipeline

The complete blind extraction pipeline. **The original image is not used or required.**

```
INPUT: Image to verify (any format)

Step 1:  Preprocessing (identical to embedding Step 1)
         -> EXIF rotation -> Alpha removal -> Resize to 512x512
         -> RGB to YCbCr -> Extract Y channel (float32, [0,255])

Step 2:  DWT decomposition
         -> LL, (LH, HL, HH) = pywt.dwt2(Y_channel, 'haar')

Step 3:  Generate block sequence (identical to embedding Step 6)
         -> rng = random.Random(0x574D5031)
         -> indices = list(range(1024)); rng.shuffle(indices)

Step 4:  For each copy c in [0,4]:
         For each block position k in [0,191]:
             block_idx = copy_blocks[c][k]
             row = block_idx // 32; col = block_idx % 32
             Extract 8x8 block from HL at (row*8, col*8)
             Apply 2D DCT (norm='ortho')
             extracted_bit[c][2*k]   = qim_extract(dct_block[3][4], Delta)
             extracted_bit[c][2*k+1] = qim_extract(dct_block[4][3], Delta)

Step 5:  Majority vote across 5 copies
         For each bit position i in [0, 383]:
             votes = sum(extracted_bit[c][i] for c in [0,4])
             majority_bits[i] = 1 if votes >= 3 else 0

Step 6:  De-interleaving
         -> reshape majority_bits (384 bits) to 8x48 matrix (row-major)
         -> read row-major -> 384-bit de-interleaved sequence
         -> = candidate RS-encoded codeword (48 bytes)

Step 7:  Reed-Solomon decoding
         -> rs = RSCodec(nsym=24)
         -> try: decoded_msg, _, _ = rs.decode(candidate_bytes)
         -> if RSCodecError: mark as UNRECOVERABLE; stop

Step 8:  Magic header validation
         -> magic = int.from_bytes(decoded_msg[0:4], 'big')
         -> if magic != 0x574D5031: verdict = NO_WATERMARK_FOUND; stop

Step 9:  CRC validation
         -> computed_crc = binascii.crc32(decoded_msg[:20]) & 0xFFFFFFFF
         -> stored_crc   = int.from_bytes(decoded_msg[20:24], 'big')
         -> if computed_crc != stored_crc: verdict = NO_WATERMARK_FOUND; stop

Step 10: UUID extraction
         -> uuid_bytes = decoded_msg[4:20]
         -> provenance_id = uuid.UUID(bytes=uuid_bytes)

Step 11: Database lookup
         -> query PostgreSQL for provenance record by provenance_id
         -> if not found: verdict = NO_WATERMARK_FOUND; stop

Step 12: SHA-256 comparison
         -> submitted_hash = sha256(submitted_image_file_bytes)
         -> registered_hash from provenance record

         if submitted_hash == registered_hash:
             verdict = AUTHENTIC_UNMODIFIED
         else:
             verdict = TRACED_BUT_MODIFIED

OUTPUT: verdict + provenance_id (if found) + registered metadata
```

---

## 12. Image Quality Acceptance Criteria

### 12.1 Minimum Thresholds

```
PSNR_MIN = 35.0   # dB
SSIM_MIN = 0.95   # unitless, range [0,1]
```

These are hard acceptance criteria. A watermarked image that does not meet both thresholds at the chosen Delta value is **rejected**. The Delta value must be reduced until the thresholds are met on the test set.

### 12.2 Measurement Protocol

- **Reference:** Original AI-generated image (before watermarking), normalized to 512 x 512 and converted to Y channel.
- **Test:** Watermarked image (after embedding), same normalization, same Y channel.
- **PSNR:** Computed on the Y channel only. Formula: `PSNR = 10 * log10(255^2 / MSE)` where MSE is the mean squared error per pixel over all 512 x 512 = 262144 pixels.
- **SSIM:** Computed on the Y channel only using `skimage.metrics.structural_similarity(original_Y, watermarked_Y, data_range=255)`.
- **Test set:** Minimum 5 diverse images (see Section 13 for test image requirements).

### 12.3 These Are Targets, Not Results

The values PSNR >= 35 dB and SSIM >= 0.95 are **acceptance thresholds to be verified by experiment**, not claimed or pre-determined results. No PSNR or SSIM value may be stated in any report, presentation, or documentation until it has been measured on real watermarked images during Phase 2 robustness experiments.

Similarly, the following robustness targets are **targets**, not achieved results:
- 100% payload extraction from lossless PNG copy
- >= 95% bit accuracy (post-ECC) from JPEG Q90
- Successful payload extraction from JPEG Q75

**Fabricating experimental results — including copying values from this specification document as if they were measured — is a serious academic integrity violation. All values reported in Phase 2 must be produced by running the actual code on real images.**

---

## 13. Robustness Scope

### 13.1 MVP Robustness Tests

The following transformations are tested as part of the MVP acceptance criteria. The system MUST be able to extract the watermark (or gracefully report `WATERMARK_UNRECOVERABLE`) for each:

| Transformation | Description | Success Criterion |
|---|---|---|
| JPEG Q90 | PNG -> JPEG (quality=90) -> PNG | UUID recovered >= 95% bit accuracy post-ECC |
| JPEG Q75 | PNG -> JPEG (quality=75) -> PNG | UUID recovered (ECC absorbs errors) |
| PNG -> JPEG -> PNG | Full format conversion cycle at Q90 | UUID recovered |
| Resize 50% | 512->256->512 (LANCZOS) | UUID recovered |
| Resize 75% | 512->384->512 (LANCZOS) | UUID recovered |
| Resize 150% | 512->768->512 (LANCZOS) | UUID recovered |
| Brightness +20 | Add 20 to all pixels, clip to [0,255] | UUID recovered |
| Gaussian noise | sigma=5, additive, clip to [0,255] | UUID recovered |

"UUID recovered" means: RS decoding succeeds, magic header matches, CRC validates, and UUID is extracted without error.

### 13.2 Experimental-Only Tests (Not MVP Criteria)

| Transformation | Status |
|---|---|
| JPEG quality 50 | Experimental only. May fail; not a requirement. |
| 10% center crop + resize | Experimental only. Shifts block grid; extraction unlikely. |
| 25% crop | Experimental only. |
| 90-degree rotation | Experimental only. |
| Text overlay | Experimental only. |
| Adversarial removal | Out of scope for MVP. |

### 13.3 Explicit Limitations

The following claims MUST NOT be made about this system:

> ~~"The watermark cannot be removed."~~

> ~~"The watermark survives all image transformations."~~

> ~~"The system can detect deepfakes."~~

Correct framing:

> "The system is designed to preserve provenance information under common, non-adversarial image transformations. A determined adversary with knowledge of the algorithm may be able to destroy the watermark."

### 13.4 Test Image Requirements

The test set for Phase 2 must include at minimum:

1. AI-generated photorealistic image (Stable Diffusion)
2. AI-generated illustration / cartoon-style image
3. Natural photograph (non-AI, for comparison)
4. High-detail image (dense textures, complex patterns)
5. Low-detail image (smooth gradients, large uniform regions)

This diversity ensures the watermark system is not calibrated only for one type of image content.

---

## 14. Verification Verdict System

### 14.1 Four Verdict States

The system uses exactly four verdict states:

#### AUTHENTIC_UNMODIFIED

```
Condition: watermark extracted successfully
           AND magic header matches
           AND CRC validates
           AND UUID found in provenance registry
           AND SHA-256(submitted_file) == registered_SHA-256
```

Meaning: The submitted file is byte-for-byte identical to the registered watermarked file. No modifications have been made since registration.

#### TRACED_BUT_MODIFIED

```
Condition: watermark extracted successfully
           AND magic header matches
           AND CRC validates
           AND UUID found in provenance registry
           AND SHA-256(submitted_file) != registered_SHA-256
```

Meaning: The submitted image can be linked to a registered provenance record, but it has been modified since registration (e.g., JPEG compression, resizing, brightness adjustment, or cropping). This is NOT necessarily evidence of malicious tampering — it may reflect legitimate distribution-related transformations.

#### WATERMARK_UNRECOVERABLE

```
Condition: RS decoding fails (RSCodecError)
           OR majority vote confidence is insufficient
           OR the image has been partially matched to a provenance record
             but the watermark cannot be fully decoded
```

Meaning: The watermark signal is present but cannot be decoded reliably. The image may have been severely transformed, or it may have never been watermarked. **This is not proof of forgery.**

#### NO_WATERMARK_FOUND

```
Condition: magic header does not match 0x574D5031
           OR CRC does not validate
           OR no provenance record found for the extracted UUID
```

Meaning: No valid provenance watermark was found. The image is either not registered with this system, or has been processed in a way that destroyed the watermark, or was never watermarked. **This is not proof that the image is fake.**

### 14.2 Required UI Language

| Verdict | Required Display Text |
|---|---|
| AUTHENTIC_UNMODIFIED | "Provenance verified. This image matches the registered watermarked copy." |
| TRACED_BUT_MODIFIED | "Provenance traced. This image is linked to a registered record, but it has been modified since registration." |
| WATERMARK_UNRECOVERABLE | "Watermark could not be read. The image may have been heavily processed. Result is inconclusive." |
| NO_WATERMARK_FOUND | "No registered watermark found. This image is not linked to a record in this system." |

### 14.3 Prohibited Claims

The UI and API responses MUST NOT make the following claims:

- "This image is fake."
- "This image has been tampered with." (for `TRACED_BUT_MODIFIED`)
- "This watermark removal is malicious."

---

## 15. SHA-256 Integrity Layer

### 15.1 Role of SHA-256

SHA-256 is used to detect exact file-level modification. It is **not** the provenance identifier.

```
Watermark UUID:  answers "which provenance record does this image belong to?"
SHA-256 hash:    answers "are these exact file bytes identical to the registered file?"
```

These are complementary, not interchangeable.

### 15.2 Two Hashes Registered

At registration time, two SHA-256 hashes are computed and stored:

```
original_hash_sha256:    SHA-256 of the original AI-generated image (before watermarking)
                         Used for internal auditing only.

registered_hash_sha256:  SHA-256 of the final watermarked PNG file
                         Used for verification comparison.
```

### 15.3 SHA-256 Limitations

- SHA-256 changes when the image is JPEG-compressed, resized, or modified in any pixel.
- A JPEG export of the registered PNG will produce a different SHA-256 and yield `TRACED_BUT_MODIFIED`, not `AUTHENTIC_UNMODIFIED`.
- SHA-256 is a file-integrity check, not proof of authorship.

### 15.4 Implementation

```python
import hashlib

def compute_sha256(file_path: str) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha256.update(chunk)
    return sha256.hexdigest()
```

---

## 16. Cryptographic Authenticity Limitation

### 16.1 What the Watermark Payload Provides

The MVP watermark payload contains:

```
MAGIC (32 bits)  +  PROVENANCE UUID (128 bits)  +  CRC-32 (32 bits)
```

The CRC-32 is an error-detection code over the magic and UUID fields. It detects accidental bit corruption introduced by image transformations and allows the extractor to reject randomly corrupted payloads with high probability.

### 16.2 What the Watermark Payload Does NOT Provide

The CRC-32 is **not a cryptographic authentication mechanism**. Specifically:

- **It is not a MAC (Message Authentication Code).** CRC-32 has no secret key and cannot authenticate the source of the payload.
- **It is not a digital signature.** No public/private key infrastructure is involved.
- **It does not prevent payload forgery.** Because the embedding algorithm, the coefficient positions, the block permutation seed, and the payload structure are all public, a technically capable attacker who obtains a legitimate UUID could theoretically construct a different image containing that UUID. Such an image would pass watermark extraction, magic validation, and CRC validation. Whether it would then pass the SHA-256 hash comparison depends on whether the attacker can reproduce the exact registered watermarked PNG bytes.

### 16.3 Correct Interpretation of Verification Results

Given this limitation, verification results must be interpreted as follows:

| Result | Correct Interpretation |
|---|---|
| Watermark recovered | The embedded UUID was decoded from the image. |
| UUID found in registry | A provenance record exists for this UUID. |
| SHA-256 match | The submitted file is byte-for-byte identical to the registered watermarked PNG. |
| All three combined | The image matches the registered watermarked file. This is a strong indication of authenticity under normal (non-adversarial) use. |

None of these results constitute **cryptographic proof of authorship**. The system is designed for provenance tracing in non-adversarial environments, not for adversarial authentication.

### 16.4 Future Work

A future security extension may add a keyed MAC or digital signature over the payload to provide cryptographic authentication. This would require:
- A secret key per registration (or per user).
- Storing the verification key (or public key) in the provenance registry.
- A larger payload (beyond 192 bits) to accommodate the signature.

This is out of scope for the MVP. **Do not modify the 192-bit payload now.**

### 16.5 Required Documentation Language

Any documentation, presentation, or report must describe the system's authentication property as:

> "The system provides provenance tracing under normal, non-adversarial use. The embedded CRC detects accidental data corruption but does not constitute cryptographic proof of authorship."

The following claims are **prohibited**:

> ~~"The watermark cryptographically proves ownership."~~

> ~~"The CRC ensures the watermark cannot be forged."~~

> ~~"Watermark recovery proves the image is authentic."~~

---

## 17. Report Alignment Notes

This section documents decisions where this specification diverges from or clarifies the original project report (BITE314L, Fall 2026-27).

### 16.1 FFmpeg

**Report:** Lists FFmpeg as a multimedia technology in the technology summary table.  
**This specification:** FFmpeg is excluded from the MVP implementation.  
**Rationale:** FFmpeg is a video and audio processing library. The MVP is image-only. FFmpeg is reserved for the future video watermarking extension.

### 16.2 Neural Watermarking

**Report:** Lists "Robust Neural Watermarking" alongside DWT-DCT in the technology summary.  
**This specification:** Neural watermarking (e.g., HiDDeN, Stable Signature, Tree-Ring) is not part of the MVP.  
**Rationale:** Neural watermarking requires training or running deep neural networks, which is an entirely separate engineering effort from implementing a classical DWT-DCT signal processing pipeline. The report's methodology section and design description consistently describe DWT-DCT. The reference to neural watermarking in the technology table is interpreted as a future direction. Implementing neural watermarking in the MVP would add months of work without advancing the core provenance contribution.

### 16.3 AI Image Generation Providers

**Report:** Mentions "Stable Diffusion with GPT APIs" as if both are implemented simultaneously.  
**This specification:** The MVP uses exactly one AI image generation provider. The backend is designed to allow a second provider to be added later without architectural changes.  
**Rationale:** Supporting two provider integrations doubles the work without demonstrating additional provenance capability. Provenance tracking is agnostic to the image generator. The system also allows uploading a user-provided image instead of generating one via API, which further decouples the provenance system from AI provider availability.

### 16.4 Feature Analysis

**Report:** Describes a "Feature Analysis" step where the system identifies suitable embedding regions per image.  
**This specification:** The embedding uses a fixed HL subband and fixed coefficient positions (3,4) and (4,3), determined by signal processing analysis rather than per-image computation.  
**Rationale:** Adaptive per-image region selection is a research-level optimization. For the MVP, fixed positions chosen by signal property analysis (mid-frequency, mid-band, good JPEG robustness tradeoff) are sufficient and deterministic. Adaptive selection is reserved for future work.

### 16.5 Verification Verdict

**Report:** Describes verification as "any mismatch indicates possible tampering."  
**This specification:** Uses the four-state verdict model: `AUTHENTIC_UNMODIFIED`, `TRACED_BUT_MODIFIED`, `WATERMARK_UNRECOVERABLE`, `NO_WATERMARK_FOUND`.  
**Rationale:** The binary "match/no-match" model conflates three different situations:
1. Legitimate modifications (JPEG compression, resizing) that change the hash but not the provenance.
2. Watermark destruction that makes the result inconclusive rather than "tampered."
3. Images never registered with the system.
The four-state model accurately describes each situation without misleading the user.

---

## 18. Implementation Constants Reference

All of the following constants MUST be defined in a single file: `watermark/config.py`. No other module may redefine them.

Note: `DELTA_INITIAL = 30` is a **starting value for experiments only**. The final value must be determined by Phase 2 measurements. Do not treat this constant as a final, optimized parameter.

```python
# watermark/config.py

# Image standard
CANONICAL_WIDTH  = 512
CANONICAL_HEIGHT = 512

# DWT
DWT_WAVELET = 'haar'
DWT_LEVEL   = 1
DWT_SUBBAND = 'HL'

# DCT
DCT_BLOCK_SIZE = 8
DCT_COEFF_POS_1 = (3, 4)   # row, col (zero-indexed in 8x8 block)
DCT_COEFF_POS_2 = (4, 3)   # row, col (zero-indexed in 8x8 block)

# QIM
DELTA_INITIAL = 30          # Starting value; tune experimentally

# Payload
WATERMARK_MAGIC  = 0x574D5031   # b'WMP1'
PAYLOAD_BITS     = 192
PAYLOAD_BYTES    = 24
MAGIC_BYTES      = 4
UUID_BYTES       = 16
CRC_BYTES        = 4

# Reed-Solomon
RS_NSYM        = 24     # number of parity symbols
RS_K           = 24     # number of data symbols
RS_N           = 48     # total codeword symbols

# Repetition
REPETITIONS = 5

# Block allocation
TOTAL_BLOCKS        = 1024
BLOCKS_PER_RS_COPY  = 192    # RS_N * (8 / BITS_PER_BLOCK) = 48 * 4
BLOCKS_USED         = 960    # REPETITIONS * BLOCKS_PER_RS_COPY
BLOCK_SELECT_SEED   = 0x574D5031

# Quality acceptance thresholds
PSNR_MIN_DB  = 35.0
SSIM_MIN     = 0.95
```

---

*End of watermark_design.md*

---

**Document revision history:**

| Version | Change |
|---|---|
| 1.0 | Initial specification |
| 1.1 | Correction 1: Removed incorrect QIM distortion bound (`|c_wm - c| <= Delta`); replaced with correct data-dependent description. Correction 2: Demoted JPEG Q-table analysis from proof to initial heuristic; added requirement that all robustness figures must be measured. Correction 3: Added Section 16 — Cryptographic Authenticity Limitation. Correction 4: Renamed block permutation section to "Deterministic Public Block Permutation"; added security note that `random.Random` is not cryptographically secure. Correction 5: Reinforced that all PSNR, SSIM, and extraction accuracy values are targets to be measured, not pre-determined results; added explicit fabrication warning. |
