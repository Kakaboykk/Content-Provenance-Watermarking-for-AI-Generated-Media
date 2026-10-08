# Crop Robustness Implementation

## 1. Root Cause of Crop Failure
The fundamental cause of watermark failure after geometric cropping is spatial misalignment. The Phase 0/1 watermark embeds data in the high-frequency (HL) subband of a Haar Discrete Wavelet Transform (DWT), modifying 8x8 DCT blocks at specific spatial coordinates. The Haar DWT is completely shift-variant. A spatial shift of even 1 pixel alters the local 2x2 DWT coefficients, and by extension, corrupts the downstream 8x8 DCT block grid. Consequently, cropping the image effectively shifts the origin `(0,0)`, destroying the exact physical alignment required to recover the QIM payload.

## 2. Extraction-Side Crop-Search Strategy
To achieve crop robustness without modifying the frozen embedding algorithm, we implemented a **Spatial Crop-Search Pipeline** in `watermark/extract.py`. When an image is smaller than the canonical 512x512 grid, the extractor now treats the submitted image as a sliding window. It systematically tests possible `(dx, dy)` origin offsets, placing the cropped image onto a 512x512 canvas at each candidate location and attempting blind extraction. 

Critically, instead of zero-padding the missing canvas—which introduces severe high-frequency boundary artifacts that overwrite the delicate DCT adjustments—the missing border regions are reconstructed using `cv2.BORDER_REFLECT`.

## 3. Search Space
The search space is bounded by the difference between the canonical 512x512 size and the uploaded image size.
For an uploaded image of size `(w, h)`:
- `dx_max = 512 - w`
- `dy_max = 512 - h`

To avoid a prohibitive $O(N^2)$ brute-force search over all possible pixels, the candidate generation is structured sequentially:
1. **High-Probability Anchors**: The exact center `(dx_max // 2, dy_max // 2)` and the four corners `(0,0), (dx_max,0), (0,dy_max), (dx_max,dy_max)` are tested first.
2. **Grid Sweep**: If the anchors fail, the algorithm sweeps the remaining `[0, dx_max] x [0, dy_max]` grid using a step size of 2 pixels (since the Haar DWT operates on 2x2 windows, a 1-pixel shift is mathematically misaligned anyway).

## 4. Candidate Validation
For each candidate offset, the 512x512 padded image is passed through the standard extraction pipeline. We do not accept random data that happens to match a magic header. A candidate is only accepted if it mathematically passes:
1. The 32-bit CRC check of the extracted payload.
2. The Reed-Solomon (RS) error correction decoding (capable of correcting up to 25% corruption).
3. The recovered payload contains a valid 128-bit UUID format.

Once a candidate yields a valid payload, the search instantly halts and returns the recovered UUID. The overarching `/verify` route subsequently recognizes that the file's SHA-256 hash has changed and correctly issues a `TRACED_BUT_MODIFIED` verdict.

## 5. Supported Crop Boundary
Empirical testing on real-world crops demonstrates that the extraction successfully survives up to a **10% geometric crop**.
At 15% cropping, the physical deletion of image data exceeds the 25% Reed-Solomon parity correction limit (as the randomly distributed payload blocks are physically cut out of the image), rendering the watermark mathematically irrecoverable regardless of spatial alignment.

**Test Matrix Results:**
- Original 512x512: `AUTHENTIC_UNMODIFIED`
- 5% Crop: `TRACED_BUT_MODIFIED`
- 10% Crop: `TRACED_BUT_MODIFIED`
- 15% Crop: `WATERMARK_UNRECOVERABLE`

## 6. Crop-Position Dependence
Because the payload is pseudo-randomly dispersed across the entire 1024-block grid, the exact position of the crop (Center vs. Corners) has negligible impact on the survival of the bits. As long as the *total area* of the crop does not exceed the Reed-Solomon budget (roughly 10% geometric loss), the watermark remains fully recoverable from any corner or center origin. 

## 7. Runtime Impact
- **Untouched 512x512 images**: Zero performance impact. The pipeline bypasses crop-search completely.
- **Top-Left Crops**: ~140ms. The `scale_search` component naturally zero-pads to the top-left, inadvertently finding the alignment immediately before `crop_search` is even invoked.
- **Other Successful Crops (5-10%)**: ~800ms - 1000ms. The search successfully finds the alignment quickly via the high-probability anchor tests (e.g., Center, Corners).
- **Failed Crops (15%+)**: ~30s+. If the watermark is mathematically destroyed, the search is forced to exhaust the entire candidate grid (1,500+ iterations) before yielding `WATERMARK_UNRECOVERABLE`.

## 8. Limitations
The primary limitation is the hard mathematical ceiling at 10-12% cropping. Since the DWT payload blocks are distributed globally, any crop inherently deletes payload data. The current Reed-Solomon configuration (`RS_NSYM = 24`) allows for a maximum of 12 byte errors (25%), meaning we can physically lose at most ~12% of the image border before the data is permanently lost. Additionally, exhausting the search grid for a severely cropped image blocks the verification thread for up to 30 seconds.

## 9. Why the Embedding Specification Was Not Changed
The current embedding mechanism (Phase 0) relies on a deterministic PRNG seed to scatter blocks over a fixed 512x512 grid. Modifying this would require introducing explicit spatial synchronization markers (e.g., a visible boundary box, a log-polar Fourier transform mapping, or SIFT keypoint anchoring). Such changes constitute a complete ground-up redesign of the cryptographic protocol and would break backwards compatibility with all previously registered assets, directly violating the frozen specification constraints.
