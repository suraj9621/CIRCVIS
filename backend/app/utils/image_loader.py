"""Shared image loading for all prediction endpoints."""

import io
import logging

import cv2
import numpy as np
from PIL import Image, ImageOps

from ..utils.helpers import ImageProcessor

logger = logging.getLogger(__name__)


def load_image_from_upload(contents: bytes) -> np.ndarray:
    """
    Prepare uploaded/camera image for model inference.
    Handles:
    - JPEG/PNG from file uploads
    - JPEG from camera streams
    - Proper EXIF rotation
    - RGB conversion
    
    Returns: uint8 RGB numpy array in full resolution
    """
    try:
        image = Image.open(io.BytesIO(contents))
        
        # Fix EXIF rotation (important for phone uploads)
        image = ImageOps.exif_transpose(image)
        
        # Convert to RGB if needed
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Convert to numpy uint8
        img_array = np.array(image, dtype=np.uint8)
        
        # Validate shape
        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
            logger.error(f"Invalid image shape after conversion: {img_array.shape}")
            raise ValueError(f"Expected RGB image, got shape {img_array.shape}")
        
        logger.debug(f"Loaded image: shape={img_array.shape}, dtype={img_array.dtype}")
        return img_array
        
    except Exception as e:
        logger.error(f"Failed to load image from bytes: {e}")
        raise ValueError(f"Invalid image data: {str(e)}")


def load_image_from_pil(image: Image.Image) -> np.ndarray:
    """
    Prepare PIL image for model inference.
    Handles EXIF rotation and RGB conversion.
    """
    try:
        # Fix EXIF rotation
        image = ImageOps.exif_transpose(image)
        
        # Convert to RGB
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        img_array = np.array(image, dtype=np.uint8)
        
        if len(img_array.shape) != 3 or img_array.shape[2] != 3:
            raise ValueError(f"Expected RGB image, got shape {img_array.shape}")
        
        return img_array
        
    except Exception as e:
        logger.error(f"Failed to convert PIL image: {e}")
        raise ValueError(f"Invalid PIL image: {str(e)}")
