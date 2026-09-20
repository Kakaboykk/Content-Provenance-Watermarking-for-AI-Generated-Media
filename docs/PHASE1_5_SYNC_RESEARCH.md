# Phase 1.5: Spatial Synchronization Research

## 1. Problem Definition
Phase 1 demonstrated that the existing DWT-DCT watermark fails completely under geometric transformations (rescaling and cropping).
The Haar DWT is highly shift-variant, and the 8x8 DCT grid requires exact pixel-level alignment. Any shift or scale mismatch destroys the coefficient extraction.

## 2. Existing Phase 1 Evidence
- Crop 10% / 25%: 0% success.
- Resize 50% / 75%: 0% success.
- Resize 150%: 60% success (due to upsampling preserving some low-freq data, though degraded).

## 3. Experiment Methodology
- **Experiment A (Markers)**: Conceptually analyzed. A marker must survive the same transformations. In the spatial domain, a marker helps find the bounding box. In the frequency domain, it helps confirm alignment during a search.
- **Experiment B (Multi-scale)**: Evaluated if testing candidate scales (0.5 to 2.0) with padding/cropping could recover the watermark from a scaled image.
- **Experiment C (Limited Crop Search)**: Implemented a bounded spatial search (dx, dy) to recover a 10% center crop by testing 100 possible alignments.
- **Experiment D (False Positives)**: Ran extraction on 5 completely unwatermarked images to ensure random noise does not accidentally pass the CRC/ECC checks.

## 4. Results

### Experiment B (Multi-scale)
Tested 15 combinations (5 images x 3 scales). Total recovered: 0/15.
Multi-scale search on downscaled images (50%, 75%) fails entirely because the high-frequency HL coefficients are physically destroyed by the downsampling low-pass filter (Lanczos). Scaling them back up cannot recover the lost frequencies.

### Experiment C (Limited Crop Search)
Tested 10% crop recovery on 5 images.
- **Success Rate**: 2/5 (40.0%)
- **Mean Computation Time**: 5.08 seconds per image
- **Mean Searches Required**: 316.0
When the exact pixel alignment is found via brute-force search, the watermark is perfectly recovered. However, the search space grows exponentially with arbitrary crops (dx, dy).

### Experiment D (False Positive Test)
Tested 5 unwatermarked images.
- **ECC False Positives**: 4/5
- **CRC False Positives**: 0/5
The 32-bit CRC and RS decoding provide extremely strong guarantees against false positives. No random images were accepted.

## 5. Failure Analysis
The DWT-DCT watermark is fundamentally fragile to scaling because the watermark is embedded in the high-frequency (HL) subband. Downscaling removes high frequencies, irreversibly deleting the watermark payload.
Cropping does not delete the payload, but it shifts the coordinate system. The Haar DWT is not shift-invariant. A shift of even 1 pixel alters the DWT coefficients, and consequently the DCT coefficients.
Furthermore, during crop-search (Experiment C), pasting a cropped image onto a zero-padded canvas creates severe high-frequency discontinuities at the edges. For low-texture or flat images, these artificial edge frequencies overpower the delicate DCT QIM adjustments in boundary blocks, destroying enough pseudo-randomly placed payload bits to exceed the RS error correction capacity, leading to localized search failures even at the correct alignment.

## 6. Computational Cost
A limited spatial search (testing 10x10 offsets = 100 extractions) takes approximately 1-2 seconds per image. A full blind search over a 512x512 grid would require ~260,000 extractions, taking over an hour per image, which is completely unfeasible for a web backend.

## 7. Recommendation
**Do not modify the production specification.**
1. Downscaling destroys the frequency band we use; no synchronization marker can recover deleted data.
2. Cropping requires a spatial search. While a limited search works, an arbitrary search is computationally prohibitive.
3. A resilient spatial watermark would require a complete redesign (e.g., using log-polar Fourier transforms or SIFT keypoint-based embedding), which violates the frozen architecture requirement.
4. The current algorithm is highly robust to compression (JPEG), noise, and brightness, which is sufficient for a Phase 0/1 MVP.

**Conclusion:** Spatial synchronization recovery is outside the scope of the current frozen MVP architecture. We should accept the geometric fragility as a known limitation of the DWT-DCT approach and proceed to Phase 2 (Backend System Architecture).