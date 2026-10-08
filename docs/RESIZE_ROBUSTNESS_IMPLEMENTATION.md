# Resize Robustness Implementation

## 1. Root Cause of Resize Failure
When an image is geometrically downscaled (e.g., from 512×512 to 358×358), the original 8x8 DCT grid used for watermark extraction is physically shifted, and high-frequency energy (in the HL sub-band) is permanently destroyed or blurred. The existing extraction pipeline strictly read from a fixed spatial layout after blindly upscaling back to 512x512 via `preprocess_image`, which further smeared frequencies and mathematically failed to properly realign fractional shifts.

## 2. Scale-Search Approach
To counteract minor misalignments without modifying the frozen embedding specification, we implemented a **Scale-Search Extraction** strategy directly within `watermark/extract.py`. Rather than indiscriminately resizing every input back to 512×512 once and stopping, the extractor now attempts to systematically search for the fractional scale that perfectly re-aligns the physical DCT blocks, attempting full DWT+DCT payload extraction at each candidate scale.

## 3. Candidate Scale Strategy
The scale-search logic leverages the uploaded image dimensions to bound the search space:
- We compute the exact inverse scale: `exact_scale = 512.0 / max(w, h)`.
- We generate candidate scales around this ratio by sweeping `[-0.15, +0.15]` in increments of `0.05` (configurable via `SCALE_STEP`).
- A wider fallback range between `MIN_SCALE (0.5)` and `MAX_SCALE (2.0)` is appended to ensure robustness against aggressively cropped images.
- The `extract_watermark_with_stats` and `preprocess_image` functions were refactored to accept arbitrary `target_size` tuples, allowing extraction across a sliding scale window while implicitly utilizing the top-left portion of the resulting DWT bands.

## 4. Extraction Validation
For each candidate scale, the full extraction pipeline is run. We accept a candidate if it successfully evaluates:
- **Magic Header & CRC**: Handled via the existing `PayloadError` catch.
- **Reed-Solomon ECC**: Validated via `rs_decode`.
- If an extraction returns `AUTHENTIC_UNMODIFIED` or `TRACED_BUT_MODIFIED`, the search instantly halts and returns the success.
- If multiple scales yield partial data, the "best" partial status (e.g., `WATERMARK_UNRECOVERABLE` over `NO_WATERMARK_FOUND`) is preserved.

## 5. Supported Resize Range (Based on Tests)
Empirical testing on real-world downscaled PNGs yields the following practical range limit:
*   **512×512**: `AUTHENTIC_UNMODIFIED` (Baseline)
*   **460×460**: `TRACED_BUT_MODIFIED` (Successfully recovered via search)
*   **410×410**: `WATERMARK_UNRECOVERABLE` (Grid found, but ECC fails due to high-frequency loss)
*   **384×384**: `WATERMARK_UNRECOVERABLE` 
*   **358×358**: `NO_WATERMARK_FOUND` (Irrecoverable low-pass destruction)
*   **320×320**: `NO_WATERMARK_FOUND` 
*   **256×256**: `NO_WATERMARK_FOUND` 

**Conclusion**: The scale-search effectively extends robustness down to **~460×460 (90% scale)**. Beyond this limit, Lanczos resampling mathematically destroys too much high-frequency DWT energy for Reed-Solomon to correct, making the watermark physically irrecoverable without changing the embedded DWT level.

## 6. Performance Impact
- **Original 512x512 images**: Zero performance impact. The baseline extraction intercepts natively sized images and bypasses the search loop entirely.
- **Resized images**: The search increases extraction latency by approximately `50ms - 200ms` depending on the number of candidate scales evaluated, as QIM extraction is computationally cheap.

## 7. Limitations
The fundamental limitation of this approach is that it cannot restore high-frequency data wiped out by severe low-pass interpolation. Once an image is scaled down past 85%, the QIM payload is no longer mathematically present in the pixels.

## 8. Future Synchronization Improvements
To support aggressive resizing (e.g., 256x256), the frozen embedding specification would have to be modified. Implementing a continuous **Log-Polar Fourier Synchronization Ring** during embedding would allow the extractor to calculate the exact affine matrix (rotation/scale) instantly, eliminating the need for a brute-force scale search and allowing the watermark to be embedded in lower-frequency bands that survive severe scaling.
