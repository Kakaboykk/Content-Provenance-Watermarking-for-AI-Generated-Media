import numpy as np
from skimage.metrics import structural_similarity
from PIL import Image

from watermark.preprocess import preprocess_image

def calculate_psnr(original_Y: np.ndarray, watermarked_Y: np.ndarray) -> float:
    """
    Calculate PSNR between two images on the Y channel.
    Formula: PSNR = 10 * log10(255^2 / MSE)
    """
    mse = np.mean((original_Y - watermarked_Y) ** 2)
    if mse == 0:
        return float('inf')
    psnr = 10 * np.log10((255.0 ** 2) / mse)
    return psnr

def calculate_ssim(original_Y: np.ndarray, watermarked_Y: np.ndarray) -> float:
    """
    Calculate SSIM between two images on the Y channel.
    """
    ssim, _ = structural_similarity(original_Y, watermarked_Y, data_range=255.0, full=True)
    return ssim

def evaluate_image_quality(original_image: Image.Image, watermarked_image: Image.Image) -> tuple[float, float]:
    """
    Preprocess both images to extract their Y channels and calculate PSNR and SSIM.
    Returns (PSNR, SSIM).
    """
    orig_Y, _, _ = preprocess_image(original_image)
    wm_Y, _, _ = preprocess_image(watermarked_image)
    
    psnr = calculate_psnr(orig_Y, wm_Y)
    ssim = calculate_ssim(orig_Y, wm_Y)
    
    return psnr, ssim
