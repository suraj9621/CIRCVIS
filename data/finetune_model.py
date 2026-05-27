#!/usr/bin/env python3
"""
Fast fine-tuning pipeline for CIRCVIS.
Uses pretrained MobileNetV2 (ImageNet) with a lightweight head.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

import numpy as np

try:
    from tensorflow import keras
    from tensorflow.keras import layers, Model
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing.image import ImageDataGenerator
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
    from tensorflow.keras.optimizers import Adam
except ImportError:
    print("TensorFlow not installed. Run: pip install tensorflow")
    sys.exit(1)

sys.path.insert(0, str(Path(__file__).parent.parent))
from backend.app.utils.helpers import ImageProcessor

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODEL_NAME = "circvis_model"
IMG_SIZE = ImageProcessor.IMG_SIZE
NUM_CLASSES = len(ImageProcessor.CLASS_NAMES)


def build_model(freeze_until: int = -35) -> Model:
    """
    ImageNet-pretrained MobileNetV2 with minimal head.
    Default: freeze all but last 35 backbone layers + new classifier.
    """
    base = MobileNetV2(
        weights="imagenet",
        include_top=False,
        input_shape=(IMG_SIZE, IMG_SIZE, 3),
        name="backbone",
    )
    base.trainable = True
    for layer in base.layers[:freeze_until]:
        layer.trainable = False

    inputs = keras.Input(shape=(IMG_SIZE, IMG_SIZE, 3), name="image_input")
    x = base(inputs)
    x = layers.GlobalAveragePooling2D(name="global_avg_pool")(x)
    x = layers.Dropout(0.3, name="dropout")(x)
    outputs = layers.Dense(NUM_CLASSES, activation="softmax", name="predictions")(x)

    return Model(inputs=inputs, outputs=outputs, name=MODEL_NAME)


def compute_class_weights(data_dir: Path) -> dict:
    """Balance rare classes; down-weight over-predicted Miscellaneous."""
    train_dir = data_dir / "splits" / "train"
    counts = {}
    for cls in ImageProcessor.CLASS_NAMES:
        cls_dir = train_dir / cls
        if cls_dir.is_dir():
            counts[cls] = sum(
                1 for f in cls_dir.iterdir()
                if f.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".gif"}
            )
        else:
            counts[cls] = 0

    total = sum(max(c, 1) for c in counts.values())
    n = len(ImageProcessor.CLASS_NAMES)
    weights = {}
    for idx, cls in enumerate(ImageProcessor.CLASS_NAMES):
        w = total / (n * max(counts[cls], 1))
        if cls == "Miscellaneous":
            w *= 0.7
        elif cls == "Metal":
            w *= 1.2
        elif cls == "Paper_Cardboard":
            w *= 1.25
        weights[idx] = float(w)
    return weights


def create_generators(data_dir: Path, batch_size: int = 32):
    train_datagen = ImageDataGenerator(
        preprocessing_function=ImageProcessor.preprocess_image,
        rotation_range=15,
        width_shift_range=0.1,
        height_shift_range=0.1,
        horizontal_flip=True,
        zoom_range=0.1,
    )
    val_datagen = ImageDataGenerator(preprocessing_function=ImageProcessor.preprocess_image)

    common = dict(
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=batch_size,
        class_mode="categorical",
        classes=ImageProcessor.CLASS_NAMES,
    )
    train_gen = train_datagen.flow_from_directory(str(data_dir / "splits" / "train"), **common)
    val_gen = val_datagen.flow_from_directory(str(data_dir / "splits" / "val"), **common)
    return train_gen, val_gen


def evaluate_on_split(model, data_dir: Path, split: str = "test", batch_size: int = 32):
    datagen = ImageDataGenerator(preprocessing_function=ImageProcessor.preprocess_image)
    generator = datagen.flow_from_directory(
        str(data_dir / "splits" / split),
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=batch_size,
        class_mode="categorical",
        classes=ImageProcessor.CLASS_NAMES,
        shuffle=False,
    )

    loss, accuracy = model.evaluate(generator, verbose=0)
    preds = model.predict(generator, verbose=0)
    pred_classes = np.argmax(preds, axis=1)
    true_classes = generator.classes

    per_class_acc = {}
    for idx, class_name in enumerate(ImageProcessor.CLASS_NAMES):
        mask = true_classes == idx
        if mask.sum() > 0:
            per_class_acc[ImageProcessor.get_display_class_name(class_name)] = float(
                (pred_classes[mask] == idx).mean()
            )

    return {
        "split": split,
        "loss": float(loss),
        "accuracy": float(accuracy),
        "samples": int(generator.samples),
        "per_class_accuracy": per_class_acc,
    }


def finetune(data_dir: str, models_dir: str, batch_size: int = 32, epochs: int = 15):
    data_path = Path(data_dir)
    models_path = Path(models_dir)
    models_path.mkdir(exist_ok=True)

    if not (data_path / "splits" / "train").exists():
        logger.error("Train split not found. Run: python data/etl.py")
        sys.exit(1)

    train_gen, val_gen = create_generators(data_path, batch_size)
    class_weights = compute_class_weights(data_path)
    logger.info("Train: %s | Val: %s", train_gen.samples, val_gen.samples)
    logger.info("Class weights: %s", class_weights)

    model = build_model(freeze_until=-35)
    trainable = sum(int(w.trainable) for w in model.trainable_weights)
    logger.info("Total params: %s | Trainable: %s", f"{model.count_params():,}", trainable)

    model.compile(
        optimizer=Adam(learning_rate=1e-4),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks = [
        EarlyStopping(monitor="val_accuracy", patience=5, restore_best_weights=True, mode="max"),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-6),
        ModelCheckpoint(
            str(models_path / f"{MODEL_NAME}_checkpoint.keras"),
            monitor="val_accuracy",
            save_best_only=True,
            mode="max",
        ),
    ]

    logger.info("Fine-tuning MobileNetV2 for %s epochs...", epochs)
    model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=epochs,
        callbacks=callbacks,
        class_weight=class_weights,
        verbose=1,
    )

    model_path = models_path / f"{MODEL_NAME}.keras"
    model.save(str(model_path))
    logger.info("Saved model to %s", model_path)

    val_results = evaluate_on_split(model, data_path, "val")
    test_results = evaluate_on_split(model, data_path, "test")

    summary = {
        "model": MODEL_NAME,
        "backbone": "MobileNetV2 (ImageNet pretrained)",
        "architecture": "MobileNetV2 -> GlobalAvgPool -> Dropout(0.3) -> Dense(7)",
        "class_names": [ImageProcessor.get_display_class_name(c) for c in ImageProcessor.CLASS_NAMES],
        "training_config": {"epochs": epochs, "batch_size": batch_size, "learning_rate": 1e-4},
        "validation": val_results,
        "test": test_results,
    }

    with open(models_path / "training_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info("=" * 60)
    logger.info("Val accuracy : %.2f%%", val_results["accuracy"] * 100)
    logger.info("Test accuracy: %.2f%%", test_results["accuracy"] * 100)
    logger.info("=" * 60)
    return summary


def main():
    parser = argparse.ArgumentParser(description="Fast MobileNetV2 fine-tuning for CIRCVIS")
    parser.add_argument("--data", default="data/processed")
    parser.add_argument("--models", default="models")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=15)
    args = parser.parse_args()
    finetune(args.data, args.models, args.batch_size, args.epochs)


if __name__ == "__main__":
    main()
