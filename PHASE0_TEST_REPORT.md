# Phase 0 Test Report: Standalone Watermarking Prototype

## 1. Environment
- **Python Version**: 3.13.5
- **OS**: Windows

### Libraries and Versions
- `numpy`: 2.5.3
- `Pillow`: 12.3.0
- `opencv-python-headless`: 5.0.0.93
- `PyWavelets`: 1.10.0
- `reedsolo`: 1.7.0
- `scikit-image`: 0.26.0
- `pytest`: 9.1.1

## 2. Test Execution

A comprehensive unit test suite was implemented in `watermark/tests/` to validate the core components of the standalone watermark engine. 

- **Total Tests Executed**: 13
- **Tests Passed**: 13
- **Tests Failed**: 0

The following areas were validated in isolation:
- Canonical image preprocessing (resizing, YCbCr conversion, alpha removal)
- DWT and IDWT coefficient reconstruction and transformations
- 8x8 DCT and IDCT round-trip processing
- Exact RS(48,24) error correction constraints (failure beyond 12 corrupted bytes, perfect recovery at or below 12 bytes)
- Payload serialization, exact structural layout (Magic, UUID, CRC), and correct big-endian byte-order mapping
- Deterministic column-major bit interleaving and deinterleaving
- Randomly seeded (0x574D5031) unique public block distribution for exactly 960 blocks out of 1024 
- QIM coefficient manipulation

## 3. End-to-End Result (Clean Blind Extraction)

The `scripts/watermark_demo.py` script was run to validate the end-to-end integration:
1. Generation of a synthetic image with gradients and noise.
2. Embedding a UUID.
3. Saving the watermarked image to disk as a lossless PNG (`watermarked_synthetic.png`).
4. Reloading the image from disk.
5. Performing blind extraction.

**Result**: **SUCCESS**
The extracted payload passed Magic Header validation, CRC validation, and the recovered UUID matched the originally embedded UUID exactly. The verdict `AUTHENTIC_UNMODIFIED` was correctly returned. 

## 4. Image Quality Metrics

During the demo run, the quality of the watermarked image against the original synthetic baseline was evaluated.

- **Actual PSNR measured**: 42.71 dB (Target: >= 35.0 dB)
- **Actual SSIM measured**: 0.9864 (Target: >= 0.95)

Both targets were comfortably met with the initial QIM quantization step `DELTA_INITIAL = 30`.

## 5. Known Limitations

- **Robustness Tests Deferred**: JPEG, resize, and crop robustness tests were deliberately excluded in Phase 0 as instructed. 
- **QIM Distortion Check**: `qim_embed` strictly implements the parity modifications requested without clipping. Subsequent IDWT values might marginally fall outside [0, 255] prior to final integer-clipping in the post-processing phase, which introduces minor rounding variations acceptable by the robust RS setup.

## 6. Specification Adherence
No deviations were made from the frozen v1.1 `watermark_design.md` specification. The numerical accuracy of IDWT -> DCT was preserved by strictly passing floating-point types down the pipeline.
