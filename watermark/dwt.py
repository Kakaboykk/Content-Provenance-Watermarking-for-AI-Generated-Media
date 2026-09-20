import numpy as np
import pywt
from watermark.config import DWT_WAVELET

def apply_dwt(image_channel: np.ndarray) -> tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]:
    """
    Apply one-level 2D Discrete Wavelet Transform.
    
    Args:
        image_channel: The 2D image channel (float32).
        
    Returns:
        tuple containing (LL, (LH, HL, HH))
    """
    coeffs2 = pywt.dwt2(image_channel, DWT_WAVELET)
    return coeffs2

def apply_idwt(coeffs2: tuple[np.ndarray, tuple[np.ndarray, np.ndarray, np.ndarray]]) -> np.ndarray:
    """
    Apply Inverse 2D Discrete Wavelet Transform.
    
    Args:
        coeffs2: tuple containing (LL, (LH, HL, HH))
        
    Returns:
        The reconstructed 2D image channel (float32).
    """
    reconstructed = pywt.idwt2(coeffs2, DWT_WAVELET)
    # The specification says: "Clip to [0, 255] after IDWT before converting back to uint8."
    # We will do clipping during the postprocessing step or here. Let's not clip here to preserve math,
    # but the pipeline step 9 says: "-> Clip to [0, 255]". We'll let embed.py or postprocess_image handle it.
    return reconstructed
