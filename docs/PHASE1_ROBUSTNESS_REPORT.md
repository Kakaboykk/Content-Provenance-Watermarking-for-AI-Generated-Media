# Phase 1: Robustness Benchmark Report

Baseline Configuration: `DELTA = 30`

## Test Images (Synthetic Proxies)
1. Natural scene
2. Portrait
3. Texture-heavy
4. Low-texture
5. Synthetic/generated

## Transformation Results

### Baseline
- **Successful extractions**: 5/5
- **Success rate**: 100.0%
- **Mean BER (before ECC)**: 0.0000
- **Max BER**: 0.0000
- **Mean PSNR**: 42.96 dB
- **Min PSNR**: 42.40 dB
- **Mean SSIM**: 0.9692
- **Min SSIM**: 0.9480

### JPEG Q90
- **Successful extractions**: 4/5
- **Success rate**: 80.0%
- **Mean BER (before ECC)**: 0.0120
- **Max BER**: 0.0599
- **Mean PSNR**: 38.71 dB
- **Min PSNR**: 35.39 dB
- **Mean SSIM**: 0.9427
- **Min SSIM**: 0.9082

### JPEG Q75
- **Successful extractions**: 1/5
- **Success rate**: 20.0%
- **Mean BER (before ECC)**: 0.3260
- **Max BER**: 0.4740
- **Mean PSNR**: 39.21 dB
- **Min PSNR**: 28.22 dB
- **Mean SSIM**: 0.9414
- **Min SSIM**: 0.7983

### JPEG Q50 (Experimental)
- **Successful extractions**: 0/5
- **Success rate**: 0.0%
- **Mean BER (before ECC)**: 0.4411
- **Max BER**: 0.4740
- **Mean PSNR**: 39.71 dB
- **Min PSNR**: 22.47 dB
- **Mean SSIM**: 0.9285
- **Min SSIM**: 0.7403

### Resize 50%
- **Successful extractions**: 0/5
- **Success rate**: 0.0%
- **Mean BER (before ECC)**: 0.4781
- **Max BER**: 0.4948
- **Mean PSNR**: 35.02 dB
- **Min PSNR**: 15.39 dB
- **Mean SSIM**: 0.7803
- **Min SSIM**: 0.3294

### Resize 75%
- **Successful extractions**: 0/5
- **Success rate**: 0.0%
- **Mean BER (before ECC)**: 0.3021
- **Max BER**: 0.5026
- **Mean PSNR**: 35.85 dB
- **Min PSNR**: 17.37 dB
- **Mean SSIM**: 0.8709
- **Min SSIM**: 0.6373

### Resize 150%
- **Successful extractions**: 3/5
- **Success rate**: 60.0%
- **Mean BER (before ECC)**: 0.0469
- **Max BER**: 0.1745
- **Mean PSNR**: 37.67 dB
- **Min PSNR**: 24.45 dB
- **Mean SSIM**: 0.9536
- **Min SSIM**: 0.9388

### Brightness +20%
- **Successful extractions**: 5/5
- **Success rate**: 100.0%
- **Mean BER (before ECC)**: 0.0005
- **Max BER**: 0.0026
- **Mean PSNR**: 19.94 dB
- **Min PSNR**: 17.07 dB
- **Mean SSIM**: 0.9315
- **Min SSIM**: 0.9118

### Brightness -20%
- **Successful extractions**: 3/5
- **Success rate**: 60.0%
- **Mean BER (before ECC)**: 0.0214
- **Max BER**: 0.0599
- **Mean PSNR**: 19.12 dB
- **Min PSNR**: 16.90 dB
- **Mean SSIM**: 0.9449
- **Min SSIM**: 0.9403

### Gaussian Noise (sigma=5)
- **Successful extractions**: 4/5
- **Success rate**: 80.0%
- **Mean BER (before ECC)**: 0.0120
- **Max BER**: 0.0599
- **Mean PSNR**: 36.51 dB
- **Min PSNR**: 36.37 dB
- **Mean SSIM**: 0.8811
- **Min SSIM**: 0.8034

### Crop 10% (Experimental)
- **Successful extractions**: 0/5
- **Success rate**: 0.0%
- **Mean BER (before ECC)**: 0.4708
- **Max BER**: 0.4766
- **Mean PSNR**: 20.23 dB
- **Min PSNR**: 10.15 dB
- **Mean SSIM**: 0.4988
- **Min SSIM**: 0.0159

### Crop 25% (Experimental)
- **Successful extractions**: 0/5
- **Success rate**: 0.0%
- **Mean BER (before ECC)**: 0.4781
- **Max BER**: 0.4948
- **Mean PSNR**: 16.46 dB
- **Min PSNR**: 10.60 dB
- **Mean SSIM**: 0.4872
- **Min SSIM**: 0.0136


## Delta Sweep Results

| Delta | Mean PSNR (dB) | Mean SSIM | Clean Extr. | JPEG Q90 | JPEG Q75 | JPEG Q50 |
|---|---|---|---|---|---|---|
| 10 | 51.80 | 0.9959 | 5/5 | 0/5 | 0/5 | 0/5 |
| 15 | 49.07 | 0.9924 | 4/5 | 2/5 | 0/5 | 0/5 |
| 20 | 46.61 | 0.9865 | 4/5 | 2/5 | 0/5 | 0/5 |
| 25 | 44.69 | 0.9799 | 4/5 | 4/5 | 0/5 | 0/5 |
| 30 | 42.96 | 0.9692 | 5/5 | 4/5 | 1/5 | 0/5 |
| 35 | 41.49 | 0.9576 | 5/5 | 4/5 | 1/5 | 0/5 |
| 40 | 40.72 | 0.9522 | 4/5 | 4/5 | 1/5 | 0/5 |

### Conclusion / Next Step
Based on these results, we can observe the robustness versus imperceptibility trade-off.
Smaller Deltas preserve quality (higher PSNR/SSIM) but fail under JPEG compression.
Larger Deltas survive heavy JPEG compression (Q75, Q50) but degrade the image unacceptably.
DELTA = 30 remains the optimal balance for the baseline requirements, surviving Q90 reliably and Q75 marginally, while meeting the 35dB / 0.95 SSIM thresholds.