import numpy as np
import cv2

def apply_dct(block: np.ndarray) -> np.ndarray:
    """
    Apply 2D Discrete Cosine Transform to a block.
    
    Args:
        block: 2D numpy array (float32).
        
    Returns:
        The DCT coefficients.
    """
    return cv2.dct(block)

def apply_idct(dct_block: np.ndarray) -> np.ndarray:
    """
    Apply Inverse 2D Discrete Cosine Transform.
    
    Args:
        dct_block: The DCT coefficients (float32).
        
    Returns:
        The reconstructed spatial block.
    """
    return cv2.idct(dct_block)
