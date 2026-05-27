"""
Utility functions for image processing and augmentation
"""

import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image, ImageOps
from typing import Tuple, Optional


class ImageProcessor:
    """Image processing utilities"""
    
    # Standard input size for models
    IMG_SIZE = 224
    
    # Internal class labels (filesystem-safe)
    CLASS_NAMES = [
        'Plastic',
        'Organic',
        'Metal',
        'Paper_Cardboard',
        'Glass',
        'Textile',
        'Miscellaneous'
    ]
    
    # Display names for classes that are filesystem-safe internally
    CLASS_DISPLAY_MAP = {
        'Paper_Cardboard': 'Paper/Cardboard'
    }
    
    # Sustainability data per kg
    SUSTAINABILITY_DATA = {
        'Plastic': {'co2_saved': 3.5, 'recyclable': 95, 'decompose_years': 500},
        'Organic': {'co2_saved': 0.5, 'recyclable': 100, 'decompose_years': 0.5},
        'Metal': {'co2_saved': 8.0, 'recyclable': 100, 'decompose_years': 50},
        'Paper_Cardboard': {'co2_saved': 1.5, 'recyclable': 98, 'decompose_years': 0.25},
        'Glass': {'co2_saved': 2.0, 'recyclable': 100, 'decompose_years': 1000},
        'Textile': {'co2_saved': 2.5, 'recyclable': 60, 'decompose_years': 40},
        'Miscellaneous': {'co2_saved': 0.5, 'recyclable': 10, 'decompose_years': 20}
    }
    
    @staticmethod
    def load_image(image_path: str, size: Tuple[int, int] = None) -> np.ndarray:
        """Load image as RGB. Resizes only when size is provided."""
        try:
            with Image.open(image_path) as pil_img:
                pil_img = ImageOps.exif_transpose(pil_img)
                if pil_img.mode != "RGB":
                    pil_img = pil_img.convert("RGB")
                img = np.array(pil_img)
        except Exception as exc:
            raise ValueError(f"Cannot load image: {image_path}") from exc

        if size is not None:
            img = cv2.resize(img, size, interpolation=cv2.INTER_AREA)
        return img

    @staticmethod
    def resize_for_model(image: np.ndarray, size: int = None) -> np.ndarray:
        """Stretch-resize to model input — matches Keras training generators."""
        if size is None:
            size = ImageProcessor.IMG_SIZE
        return cv2.resize(image, (size, size), interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def center_crop_resize(image: np.ndarray, size: int = None) -> np.ndarray:
        """Center-crop to square then resize — matches training better for phone photos."""
        if size is None:
            size = ImageProcessor.IMG_SIZE
        h, w = image.shape[:2]
        min_dim = min(h, w)
        y0 = (h - min_dim) // 2
        x0 = (w - min_dim) // 2
        cropped = image[y0:y0 + min_dim, x0:x0 + min_dim]
        return cv2.resize(cropped, (size, size), interpolation=cv2.INTER_AREA)

    @staticmethod
    def prepare_upload_image(image: Image.Image) -> np.ndarray:
        """Fix EXIF rotation and return full-resolution RGB for inference TTA."""
        image = ImageOps.exif_transpose(image)
        if image.mode != "RGB":
            image = image.convert("RGB")
        return np.array(image)

    @staticmethod
    def prepare_upload_bytes(contents: bytes) -> np.ndarray:
        """Load bytes from upload/camera and prepare for model inference."""
        image = Image.open(BytesIO(contents))
        return ImageProcessor.prepare_upload_image(image)

    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for model inference.
        Handles both uint8 (0-255) and float (0-1) inputs.
        Applies ImageNet normalization: (x - mean) / std
        """
        # Ensure float32
        if image.dtype == np.uint8:
            image = image.astype(np.float32) / 255.0
        elif image.dtype != np.float32:
            image = image.astype(np.float32)
        
        # Ensure value range [0, 1]
        if image.max() > 1.1:
            image = image / 255.0
        
        # ImageNet normalization (mean and std from ImageNet)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        
        # Ensure image is in [H, W, 3] format
        if len(image.shape) == 2:
            image = np.stack([image] * 3, axis=-1)
        
        image = (image - mean) / std
        return image.astype(np.float32)
    
    @staticmethod
    def preprocess_batch(images: np.ndarray) -> np.ndarray:
        """Preprocess batch of images - handles variable input shapes"""
        processed = []
        for img in images:
            processed.append(ImageProcessor.preprocess_image(img))
        return np.array(processed, dtype=np.float32)
    
    @staticmethod
    def augment_image(image: np.ndarray) -> np.ndarray:
        """Data augmentation for training"""
        # Random brightness
        brightness = np.random.uniform(0.8, 1.2)
        image = np.clip(image * brightness, 0, 255).astype(np.uint8)
        
        # Random contrast
        contrast = np.random.uniform(0.9, 1.1)
        image = cv2.convertScaleAbs(image, alpha=contrast, beta=0)
        
        # Random rotation
        angle = np.random.uniform(-15, 15)
        h, w = image.shape[:2]
        center = (w // 2, h // 2)
        matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
        image = cv2.warpAffine(image, matrix, (w, h))
        
        # Random flip
        if np.random.random() > 0.5:
            image = cv2.flip(image, 1)
        
        return image
    
    @staticmethod
    def array_to_base64(image_array: np.ndarray) -> str:
        """Convert numpy array to base64 string"""
        # Convert to uint8 if needed
        if image_array.dtype != np.uint8:
            image_array = (image_array * 255).astype(np.uint8)
        
        # Convert to PIL Image
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            pil_image = Image.fromarray(image_array, mode='RGB')
        else:
            pil_image = Image.fromarray(image_array)
        
        # Convert to base64
        buffer = BytesIO()
        pil_image.save(buffer, format='PNG')
        buffer.seek(0)
        return base64.b64encode(buffer.getvalue()).decode()
    
    @staticmethod
    def base64_to_array(base64_str: str) -> np.ndarray:
        """Convert base64 string to numpy array, with EXIF fix and center crop."""
        import base64
        image_data = base64.b64decode(base64_str)
        return ImageProcessor.prepare_upload_bytes(image_data)
    
    @staticmethod
    def get_display_class_name(class_name: str) -> str:
        """Convert internal class names to display labels."""
        return ImageProcessor.CLASS_DISPLAY_MAP.get(class_name, class_name)

    @staticmethod
    def get_internal_class_name(class_name: str) -> str:
        """Convert display labels back to internal filesystem-safe class names."""
        reverse_map = {display: internal for internal, display in ImageProcessor.CLASS_DISPLAY_MAP.items()}
        return reverse_map.get(class_name, class_name)

    @staticmethod
    def get_sustainability_impact(class_name: str, count: int = 1, weight_kg: float = 0.1) -> dict:
        """Calculate sustainability impact"""
        internal_name = ImageProcessor.get_internal_class_name(class_name)
        data = ImageProcessor.SUSTAINABILITY_DATA.get(internal_name, {})
        
        return {
            'class_name': ImageProcessor.get_display_class_name(internal_name),
            'count': count,
            'weight_kg': weight_kg * count,
            'co2_saved_kg': data.get('co2_saved', 0) * weight_kg * count,
            'recyclable_percentage': data.get('recyclable', 0),
            'decompose_years': data.get('decompose_years', 0)
        }


class MetricsCalculator:
    """Calculate classification metrics"""
    
    @staticmethod
    def calculate_metrics(y_true, y_pred, class_names):
        """Calculate precision, recall, F1, and confusion matrix"""
        from sklearn.metrics import (
            confusion_matrix, precision_score, recall_score, 
            f1_score, accuracy_score
        )
        
        cm = confusion_matrix(y_true, y_pred)
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
        
        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'confusion_matrix': cm.tolist()
        }
