import numpy as np
from PIL import Image, ImageOps
import cv2

from watermark.config import CANONICAL_WIDTH, CANONICAL_HEIGHT

def preprocess_image(image: Image.Image) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Preprocess an image for watermarking according to the specification.
    
    Returns:
        tuple[np.ndarray, np.ndarray, np.ndarray]: (Y_channel, Cb_channel, Cr_channel)
        Y_channel is float32 in [0, 255].
        Cb and Cr are float32 in [0, 255] for potential reconstruction, or can be kept in uint8.
        The specification says:
        "The Y channel is used exclusively. The Cb and Cr channels pass through unmodified."
        We will return Y, Cb, Cr as float32 to be consistent with standard OpenCV conversions,
        but only Y will be modified by the watermark.
    """
    # 1. EXIF rotation and strip
    img = ImageOps.exif_transpose(image)
    
    # Strip EXIF (creating a new image without info dict)
    img_no_exif = Image.new(img.mode, img.size)
    img_no_exif.paste(img)
    img = img_no_exif

    # 2. Alpha removal
    if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
        # Convert to RGBA first to be safe
        img = img.convert('RGBA')
        background = Image.new('RGBA', img.size, (255, 255, 255))
        img = Image.alpha_composite(background, img).convert('RGB')
    
    # 3. Grayscale expansion
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 4. Resize
    img = img.resize((CANONICAL_WIDTH, CANONICAL_HEIGHT), Image.Resampling.LANCZOS)

    # Convert PIL Image to OpenCV format (numpy array)
    img_np = np.array(img) # Shape: (512, 512, 3), RGB

    # 5. Color space: RGB to YCbCr
    # OpenCV's cv2.COLOR_RGB2YCrCb uses ITU-R BT.601
    img_ycc = cv2.cvtColor(img_np, cv2.COLOR_RGB2YCrCb)

    # Note: OpenCV outputs Y, Cr, Cb. We need Y, Cb, Cr.
    Y = img_ycc[:, :, 0].astype(np.float32)
    Cr = img_ycc[:, :, 1].astype(np.float32)
    Cb = img_ycc[:, :, 2].astype(np.float32)

    return Y, Cb, Cr

def postprocess_image(Y: np.ndarray, Cb: np.ndarray, Cr: np.ndarray) -> Image.Image:
    """
    Reconstruct the RGB image from YCbCr channels.
    
    Args:
        Y: modified Y channel, float32
        Cb: original Cb channel, float32
        Cr: original Cr channel, float32
        
    Returns:
        PIL.Image.Image: The reconstructed RGB image.
    """
    # Clip Y to [0, 255]
    Y_clipped = np.clip(Y, 0, 255)
    
    # Recombine channels (OpenCV format: Y, Cr, Cb)
    img_ycc = np.stack([Y_clipped, Cr, Cb], axis=-1)
    
    # Convert to uint8
    img_ycc_uint8 = np.round(img_ycc).astype(np.uint8)
    
    # Convert back to RGB
    img_rgb = cv2.cvtColor(img_ycc_uint8, cv2.COLOR_YCrCb2RGB)
    
    return Image.fromarray(img_rgb)
