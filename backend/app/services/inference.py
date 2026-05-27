"""
Inference helpers: TTA views and probability calibration.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import cv2
import numpy as np

from ..utils.helpers import ImageProcessor

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DEFAULT_CALIBRATION_PATH = PROJECT_ROOT / "models" / "inference_calibration.json"

DEFAULT_CALIBRATION = {
    "logit_bias": {
        "Plastic": -0.5,  # Heavily reduced to prevent overprediction
        "Organic": -0.25,
        "Metal": 0.25,
        "Paper_Cardboard": 0.25,
        "Glass": 0.1,
        "Textile": 0.05,
        "Miscellaneous": 0.6,  # Heavily increased
    },
    "misc_override_margin": 0.30,
    "misc_override_min_alt": 0.15,
    "metallic_threshold": 0.45,
    "metallic_metal_boost": 2.0,
    "metallic_misc_penalty": 2.0,
    "metallic_organic_penalty": 1.0,
    "paper_threshold": 0.22,
    "paper_boost": 2.2,
    "paper_plastic_penalty": 1.4,
    "plastic_glossy_threshold": 0.25,
    "plastic_penalty_when_paper": 1.1,
    "glass_plastic_threshold": 0.25,
    "glass_plastic_penalty": 4.0,
    "glass_plastic_boost": 0.8,
    "misc_plastic_confusion_penalty": 2.0,  # Increased
    "misc_texture_threshold": 0.30,  # Lowered threshold
    "misc_roughness_boost": 2.5,  # Increased boost
}

INFERENCE_VERSION = "2.2"


def load_calibration(path: Path = DEFAULT_CALIBRATION_PATH) -> Dict:
    if not path.exists():
        return DEFAULT_CALIBRATION.copy()
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        merged = DEFAULT_CALIBRATION.copy()
        merged.update(data)
        return merged
    except Exception as e:
        logger.warning("Could not load inference calibration: %s", e)
        return DEFAULT_CALIBRATION.copy()


def compute_visual_hints(rgb_image: np.ndarray) -> Dict[str, float]:
    """
    Vision cues: metallic scrap, organic color, paper/carton (e.g. juice boxes), glossy plastic, texture.
    """
    sample = cv2.resize(rgb_image, (224, 224), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(sample, cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(sample, cv2.COLOR_RGB2GRAY)

    sat = float(hsv[:, :, 1].mean()) / 255.0
    val_std = float(gray.std()) / 128.0
    val_max = float(hsv[:, :, 2].max()) / 255.0
    hue_std = float(hsv[:, :, 0].std()) / 90.0
    edges = float(cv2.Canny(gray, 40, 120).mean()) / 255.0
    neutral = 1.0 - min(abs(float(gray.mean()) - 128.0) / 128.0, 1.0)

    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    line_score = min((float(np.abs(sobelx).mean()) + float(np.abs(sobely).mean())) / 128.0, 1.0)

    metallic = (1.0 - sat) * 0.45 + min(val_std, 1.0) * 0.3 + edges * 0.15 + neutral * 0.1
    organic = sat * min(hue_std, 1.0)

    # Printed cartons / tetra packs: color + edges, matte (not shiny bottle)
    matte = 1.0 - min(float(hsv[:, :, 2].std()) / 100.0, 1.0)
    paper_carton = (
        line_score * 0.22
        + min(hue_std, 1.0) * 0.32
        + sat * 0.28
        + matte * 0.18
    ) * (1.0 - min(metallic, 1.0) * 0.65)

    # Glossy plastic bottles/bags: high saturation + bright specular peaks
    plastic_glossy = sat * val_max * 0.55 + (1.0 - matte) * 0.25

    # NEW: Texture and roughness for Miscellaneous detection
    # Miscellaneous items often have irregular texture, varied edges
    laplacian = cv2.Laplacian(gray, cv2.CV_64F)
    texture_score = float(np.abs(laplacian).mean()) / 50.0
    texture_score = min(texture_score, 1.0)
    
    # Roughness: high edge variation suggests non-uniform surface (Misc)
    roughness = edges * 0.6 + texture_score * 0.4

    return {
        "metallic": float(np.clip(metallic, 0.0, 1.0)),
        "organic": float(np.clip(organic, 0.0, 1.0)),
        "paper_carton": float(np.clip(paper_carton, 0.0, 1.0)),
        "plastic_glossy": float(np.clip(plastic_glossy, 0.0, 1.0)),
        "saturation": float(np.clip(sat, 0.0, 1.0)),
        "roughness": float(np.clip(roughness, 0.0, 1.0)),  # NEW
        "texture": float(np.clip(texture_score, 0.0, 1.0)),  # NEW
    }


def build_tta_views(rgb_image: np.ndarray) -> List[np.ndarray]:
    """
    Multiple 224x224 views for test-time augmentation.
    Includes stretch-resize (matches training) and center-crop (better for phone photos).
    Returns list of uint8 images ready for preprocessing.
    """
    # Ensure uint8 input
    if rgb_image.dtype != np.uint8:
        if rgb_image.max() <= 1.0:
            rgb_image = (rgb_image * 255).astype(np.uint8)
        else:
            rgb_image = rgb_image.astype(np.uint8)
    
    views: List[np.ndarray] = []
    stretch = ImageProcessor.resize_for_model(rgb_image)
    crop = ImageProcessor.center_crop_resize(rgb_image)
    
    for base in (stretch, crop):
        views.append(base)
        views.append(cv2.flip(base, 1))  # Horizontal flip
    
    return views


def apply_calibration(
    probs: np.ndarray,
    calibration: Dict,
    rgb_image: Optional[np.ndarray] = None,
) -> np.ndarray:
    """Apply logit bias, visual metal cues, and Miscellaneous override heuristics."""
    probs = np.asarray(probs, dtype=np.float64)
    probs = np.clip(probs, 1e-8, 1.0)

    log_probs = np.log(probs)
    bias_map = calibration.get("logit_bias", {})
    for i, name in enumerate(ImageProcessor.CLASS_NAMES):
        log_probs[i] += float(bias_map.get(name, 0.0))

    hints = compute_visual_hints(rgb_image) if rgb_image is not None else {}
    metallic = hints.get("metallic", 0.0)
    paper_carton = hints.get("paper_carton", 0.0)
    plastic_glossy = hints.get("plastic_glossy", 0.0)
    metal_idx = ImageProcessor.CLASS_NAMES.index("Metal")
    misc_idx = ImageProcessor.CLASS_NAMES.index("Miscellaneous")
    organic_idx = ImageProcessor.CLASS_NAMES.index("Organic")
    paper_idx = ImageProcessor.CLASS_NAMES.index("Paper_Cardboard")
    plastic_idx = ImageProcessor.CLASS_NAMES.index("Plastic")
    glass_idx = ImageProcessor.CLASS_NAMES.index("Glass")

    metallic_threshold = float(calibration.get("metallic_threshold", 0.48))
    sat_mean = hints.get("saturation", 0.0)

    if metallic >= metallic_threshold and metallic > paper_carton and sat_mean < 0.38:
        log_probs[metal_idx] += float(calibration.get("metallic_metal_boost", 2.2))
        log_probs[misc_idx] -= float(calibration.get("metallic_misc_penalty", 1.8))
        log_probs[organic_idx] -= float(calibration.get("metallic_organic_penalty", 1.0))

    paper_threshold = float(calibration.get("paper_threshold", 0.24))
    if paper_carton >= paper_threshold and paper_carton >= plastic_glossy * 0.9:
        log_probs[paper_idx] += float(calibration.get("paper_boost", 2.0))
        log_probs[plastic_idx] -= float(calibration.get("paper_plastic_penalty", 1.6))
        log_probs[misc_idx] -= 0.5
    elif plastic_glossy >= float(calibration.get("plastic_glossy_threshold", 0.25)):
        log_probs[plastic_idx] += 0.6
        if metallic < metallic_threshold and plastic_glossy >= float(calibration.get("glass_plastic_threshold", 0.25)):
            log_probs[glass_idx] -= float(calibration.get("glass_plastic_penalty", 4.0))
            log_probs[plastic_idx] += float(calibration.get("glass_plastic_boost", 0.8))

    # NEW: Texture-based Miscellaneous detection
    # Miscellaneous items often have rough, textured surfaces
    roughness = hints.get("roughness", 0.0)
    texture = hints.get("texture", 0.0)
    misc_texture_threshold = float(calibration.get("misc_texture_threshold", 0.35))
    
    if roughness >= misc_texture_threshold and metallic < 0.35:
        # High roughness suggests Miscellaneous item
        log_probs[misc_idx] += float(calibration.get("misc_roughness_boost", 1.8))
        log_probs[plastic_idx] -= float(calibration.get("misc_plastic_confusion_penalty", 1.5))
        log_probs[paper_idx] -= 0.3

    calibrated = np.exp(log_probs)
    calibrated /= calibrated.sum()

    top_idx = int(np.argmax(calibrated))
    min_alt = float(calibration.get("misc_override_min_alt", 0.08))

    if top_idx == misc_idx:
        margin = float(calibration.get("misc_override_margin", 0.45))
        order = np.argsort(calibrated)[::-1]
        alt_idx = int(order[1])
        if (
            calibrated[alt_idx] >= min_alt
            and calibrated[misc_idx] - calibrated[alt_idx] <= margin
        ):
            calibrated[alt_idx] = calibrated[misc_idx] + 1e-4
            calibrated /= calibrated.sum()

    top_idx = int(np.argmax(calibrated))
    if top_idx == misc_idx and metallic >= metallic_threshold:
        hard_indices = [
            ImageProcessor.CLASS_NAMES.index("Metal"),
            ImageProcessor.CLASS_NAMES.index("Glass"),
            ImageProcessor.CLASS_NAMES.index("Plastic"),
        ]
        best_hard = max(hard_indices, key=lambda i: calibrated[i])
        if calibrated[best_hard] >= min_alt:
            swap = calibrated[best_hard]
            calibrated[best_hard] = calibrated[misc_idx] + 1e-4
            calibrated[misc_idx] = swap
            calibrated /= calibrated.sum()

    top_idx = int(np.argmax(calibrated))
    if top_idx == plastic_idx and paper_carton >= paper_threshold and paper_carton >= plastic_glossy * 0.85:
        if calibrated[paper_idx] >= min_alt * 0.35:
            swap = calibrated[paper_idx]
            calibrated[paper_idx] = calibrated[plastic_idx] + 1e-4
            calibrated[plastic_idx] = swap
            calibrated /= calibrated.sum()

    return calibrated.astype(np.float32)


def format_prediction(
    probs: np.ndarray,
    inference_time_ms: float,
) -> Dict:
    class_idx = int(np.argmax(probs))
    internal_class_name = ImageProcessor.CLASS_NAMES[class_idx]
    class_name = ImageProcessor.get_display_class_name(internal_class_name)
    all_classes = {
        ImageProcessor.get_display_class_name(ImageProcessor.CLASS_NAMES[i]): float(probs[i])
        for i in range(len(ImageProcessor.CLASS_NAMES))
    }
    return {
        "class_name": class_name,
        "confidence": float(probs[class_idx]),
        "all_classes": all_classes,
        "processing_time_ms": inference_time_ms,
    }
