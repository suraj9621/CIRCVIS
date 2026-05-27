#!/usr/bin/env python3
"""Evaluate trained CIRCVIS model on test set."""

import sys
import logging
from pathlib import Path

import numpy as np

try:
    from tensorflow import keras
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
except ImportError:
    print("TensorFlow not installed")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app.utils.helpers import ImageProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def evaluate_models():
    models_dir = Path("models")
    data_dir = Path("data/processed")

    if not (data_dir / "splits" / "test").exists():
        logger.error("Test data not found")
        return

    test_datagen = ImageDataGenerator(preprocessing_function=ImageProcessor.preprocess_image)
    test_generator = test_datagen.flow_from_directory(
        str(data_dir / "splits" / "test"),
        target_size=(224, 224),
        batch_size=32,
        class_mode="categorical",
        classes=ImageProcessor.CLASS_NAMES,
        shuffle=False,
    )
    logger.info("Test samples: %s", test_generator.samples)

    results = {}

    primary_path = models_dir / "circvis_model.keras"
    if primary_path.exists():
        model = keras.models.load_model(str(primary_path), compile=False)
        model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])
        logger.info("Loaded circvis_model")
        loss, accuracy = model.evaluate(test_generator, verbose=1)
        results["circvis"] = {"loss": float(loss), "accuracy": float(accuracy)}

        logger.info("=" * 60)
        logger.info("EVALUATION RESULTS")
        logger.info("  circvis_model: %.2f%%", accuracy * 100)
        logger.info("=" * 60)
        return results

    # Legacy ensemble fallback
    models = {}
    for model_file in ["resnet50.keras", "mobilenetv2.keras", "efficientnetb0.keras"]:
        model_path = models_dir / model_file
        if model_path.exists():
            models[model_file.split(".")[0]] = keras.models.load_model(str(model_path), compile=False)

    if not models:
        logger.error("No models found")
        return

    for name, model in models.items():
        loss, accuracy = model.evaluate(test_generator, verbose=1)
        results[name] = {"loss": float(loss), "accuracy": float(accuracy)}

    if len(models) > 1:
        preds = [m.predict(test_generator, verbose=0) for m in models.values()]
        ensemble_pred = np.mean(preds, axis=0)
        ensemble_acc = float(np.mean(np.argmax(ensemble_pred, axis=1) == test_generator.classes))
        results["ensemble"] = {"accuracy": ensemble_acc}

    for name, metrics in results.items():
        logger.info("  %s: %.2f%%", name, metrics["accuracy"] * 100)

    return results


if __name__ == "__main__":
    evaluate_models()
