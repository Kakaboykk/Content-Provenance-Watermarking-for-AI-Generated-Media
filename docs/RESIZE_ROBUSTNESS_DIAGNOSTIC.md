# Resize Robustness Diagnostic Report

## A. Why the 358×358 image currently produces "No Watermark Found"
The watermark is injected into the high-frequency HL sub-band of the Discrete Wavelet Transform (DWT) at specific 8x8 Discrete Cosine Transform (DCT) blocks. 
When a 512×512 image is geometrically resized to 358×358, the verification route (`watermark/preprocess.py`) intercepts it and automatically resamples it *back* up to 512×512 using Lanczos interpolation before extraction. This process causes two critical failures:
1. **High-Frequency Smearing**: Downscaling to 358 followed by upscaling to 512 acts as a low-pass filter, permanently destroying the subtle, high-frequency energy in the HL sub-band where the QIM watermark is hidden.
2. **Spatial/Grid Misalignment**: The 8x8 DCT grid used during extraction is statically mapped. Interpolation shifts the geometric boundaries of the original pixels, causing the extracted DCT coefficients to misalign with the original embedded coefficients. The resulting bit-error rate heavily exceeds the Reed-Solomon ECC capacity, resulting in `WATERMARK_UNRECOVERABLE` or `NO_WATERMARK_FOUND`.

## B. Whether the current watermark engine was designed to support geometric resizing
**No.** The current implementation in `watermark/embed.py` and `watermark/extract.py` utilizes a strict, static spatial block map (`watermark.blocks.get_copy_blocks`) that relies on absolute 8x8 pixel alignment over a fixed 512×512 grid. It was designed to survive color manipulation (brightness, contrast, JPEG compression), but it fundamentally assumes geometric pixel-perfect alignment.

## C. Whether Phase 1.5 spatial synchronization is currently active in the production verification path
**No.** A review of the production `extract_watermark_with_stats` pipeline confirms that zero spatial synchronization is being applied. The pipeline jumps straight from DWT decomposition to static block extraction without attempting to locate sync markers or realign the image. 

## D. Which existing component should be changed to support resize robustness
The extraction logic in `watermark/extract.py` and potentially the preprocessing logic in `watermark/preprocess.py` need to be modified to incorporate alignment or scale-search heuristics before attempting extraction.

## E. The smallest safe implementation change
The absolute minimum architectural change to support resizing (without breaking the frozen embedding spec) is a **Scale & Crop Search Extraction** (brute-force extraction). 
Because the QIM extraction step is computationally cheap, the verifier can attempt to extract the watermark across a sliding window of slight scales and translations (e.g., if ECC fails, translate the grid by ±1, ±2 pixels, or attempt slightly different upscaling algorithms/sharpening). 
Alternatively, the most robust architectural change would require modifying the frozen spec to embed a resilient frequency-domain **Synchronization Template** (like a Log-Polar Fourier transform marker) to mathematically calculate the affine transformation and reverse it before extraction.

## F. Expected effect on the existing 109+ tests and robustness tests
If we implement a brute-force scale/shift search in `extract.py`:
- Existing unit tests that pass perfectly aligned images will continue to pass instantly on the first extraction attempt (no performance penalty).
- The `robustness_test.py` resize tests (like the 256×256 test) might start passing, increasing the overall robustness score.
- Server latency will increase slightly *only* for images that fail the initial extraction attempt.

## G. Whether the existing frozen watermark specification would need to change
- **No**, if we use a brute-force extraction search (the embedding spec remains 100% frozen).
- **Yes**, if we implement spatial synchronization markers. We would have to modify `embed.py` to inject the synchronization markers, which violates the strict constraint to leave the Phase 0-5 watermark algorithm untouched.

---

### Appendix: Diagnostic Resize Test Results (Scale Down -> Upscale to 512)
| Target Size | Verifier Output           | UUID Recovered? | AI Detect |
|-------------|---------------------------|-----------------|-----------|
| 512×512     | `AUTHENTIC_UNMODIFIED`    | Yes             | N/A       |
| 460×460     | `TRACED_BUT_MODIFIED`     | Yes             | N/A       |
| 410×410     | `WATERMARK_UNRECOVERABLE` | No              | N/A       |
| 384×384     | `WATERMARK_UNRECOVERABLE` | No              | N/A       |
| 358×358     | `WATERMARK_UNRECOVERABLE` | No              | N/A       |
| 320×320     | `NO_WATERMARK_FOUND`      | No              | N/A       |
| 256×256     | `NO_WATERMARK_FOUND`      | No              | N/A       |

**Conclusion:** The exact threshold of failure is approximately an 85% scale (around 430×430). Below this, the interpolation completely desynchronizes the Reed-Solomon payload.
