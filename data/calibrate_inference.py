#!/usr/bin/env python3
"""Tune inference_calibration.json from validation split."""

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
except ImportError:
    print("TensorFlow required. Activate venv and retry.")
    sys.exit(1)

from backend.app.services.model_service import ModelService
from backend.app.utils.helpers import ImageProcessor

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"
OUT_PATH = PROJECT_ROOT / "models" / "inference_calibration.json"


def main():
    val_dir = DATA_DIR / "splits" / "val"
    if not val_dir.exists():
        print("Val split missing. Run: python data/etl.py")
        sys.exit(1)

    service = ModelService(models_dir=str(PROJECT_ROOT / "models"))
    if not service.is_ready():
        print("Model not loaded.")
        sys.exit(1)

    datagen = ImageDataGenerator()
    gen = datagen.flow_from_directory(
        str(val_dir),
        target_size=(ImageProcessor.IMG_SIZE, ImageProcessor.IMG_SIZE),
        batch_size=1,
        class_mode="categorical",
        classes=ImageProcessor.CLASS_NAMES,
        shuffle=False,
    )

    misc_idx = ImageProcessor.CLASS_NAMES.index("Miscellaneous")
    misc_fp = {c: 0 for c in ImageProcessor.CLASS_NAMES}
    misc_fn = 0
    total = 0

    for i in range(gen.samples):
        path = gen.filepaths[i]
        true_idx = gen.classes[i]
        true_name = ImageProcessor.CLASS_NAMES[true_idx]
        raw = service._predict_probabilities(path)
        pred_idx = int(np.argmax(raw))

        total += 1
        if pred_idx == misc_idx and true_idx != misc_idx:
            misc_fp[true_name] += 1
        if true_idx == misc_idx and pred_idx != misc_idx:
            misc_fn += 1

    bias = {}
    for cls in ImageProcessor.CLASS_NAMES:
        if cls == "Miscellaneous":
            bias[cls] = -0.85
        else:
            fp_rate = misc_fp[cls] / max(total, 1)
            bias[cls] = round(min(0.5, fp_rate * 4.0), 3)

    calibration = {
        "logit_bias": bias,
        "misc_override_margin": 0.28,
        "misc_override_min_alt": 0.16,
    }

    OUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(calibration, f, indent=2)

    print(f"Saved calibration to {OUT_PATH}")
    print(json.dumps(calibration, indent=2))


if __name__ == "__main__":
    main()
