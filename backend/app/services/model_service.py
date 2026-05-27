"""
Model Service: Load, manage, and run ensemble ML models
"""

import importlib
import os
import logging
import time
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers, Model
except ImportError:
    tf = None
    keras = None

try:
    import keras as standalone_keras
except ImportError:
    standalone_keras = None

from ..utils.helpers import ImageProcessor, MetricsCalculator
from .inference import (
    apply_calibration,
    build_tta_views,
    format_prediction,
    load_calibration,
)

logger = logging.getLogger(__name__)

BaseBatchNormalization = None
if keras is not None:
    BaseBatchNormalization = layers.BatchNormalization
elif standalone_keras is not None:
    BaseBatchNormalization = standalone_keras.layers.BatchNormalization

class LegacyBatchNormalization(BaseBatchNormalization if BaseBatchNormalization is not None else object):
    def __init__(self, *args, renorm=False, renorm_clipping=None, renorm_momentum=None, **kwargs):
        kwargs.pop('renorm', None)
        kwargs.pop('renorm_clipping', None)
        kwargs.pop('renorm_momentum', None)
        if BaseBatchNormalization is not None:
            super().__init__(*args, **kwargs)

    @classmethod
    def from_config(cls, config):
        config = config.copy()
        config.pop('renorm', None)
        config.pop('renorm_clipping', None)
        config.pop('renorm_momentum', None)
        return super().from_config(config)


def _patch_legacy_keras_loader(keras_loader):
    """Patch legacy Keras layer deserialization for older model configs."""
    legacy_keys = {'renorm', 'renorm_clipping', 'renorm_momentum', 'quantization_config'}

    def make_from_config(orig_from_config):
        def from_config(cls, config):
            config = config.copy()
            for key in legacy_keys:
                config.pop(key, None)
            return orig_from_config(config)
        return classmethod(from_config)

    # Patch core layer classes in the active Keras loader
    for layer_name in ('BatchNormalization', 'Dense'):
        layer_cls = getattr(getattr(keras_loader, 'layers', None), layer_name, None)
        if layer_cls is not None and hasattr(layer_cls, 'from_config'):
            orig_from_config = layer_cls.from_config
            try:
                layer_cls.from_config = make_from_config(orig_from_config)
            except Exception:
                pass

    # Patch source modules, when available, to support legacy class paths
    try:
        dense_mod = importlib.import_module('keras.src.layers.core.dense')
        dense_mod.Dense.from_config = getattr(keras_loader.layers, 'Dense').from_config
    except Exception:
        pass
    try:
        bn_mod = importlib.import_module('keras.src.layers.normalization.batch_normalization')
        bn_mod.BatchNormalization.from_config = getattr(keras_loader.layers, 'BatchNormalization').from_config
    except Exception:
        pass


class ModelService:
    """
    Ensemble Model Service
    Manages ResNet50, MobileNetV2, EfficientNetB0 ensemble
    """
    
    def __init__(self, models_dir: str = "models"):
        """Initialize model service"""
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True)
        
        self.class_names = ImageProcessor.CLASS_NAMES
        self.num_classes = len(self.class_names)
        
        self.models = {}
        self.ensemble_weights = None
        self.model_stats = {}
        self.load_error: Optional[str] = None
        self.calibration = load_calibration(self.models_dir / "inference_calibration.json")

        # Try to load pre-trained models
        self._load_models()
        if not self.models:
            self._set_load_error()
    
    def _set_load_error(self):
        """Set a user-facing reason when no model could be loaded."""
        model_file = self.models_dir / "circvis_model.keras"
        if tf is None and standalone_keras is None:
            self.load_error = (
                "TensorFlow install nahi hai. run.bat chalao ya: "
                "pip install tensorflow-cpu==2.21.0"
            )
        elif not model_file.exists():
            self.load_error = (
                "Model file missing. Run: python data/finetune_model.py"
            )
        elif self.load_error is None:
            self.load_error = (
                "Model file hai par load nahi hua. Server restart karo ya run.bat dubara chalao."
            )

    def _load_models(self):
        """Load pre-trained models from disk"""
        keras_loader = standalone_keras or keras
        if keras_loader is None:
            logger.warning("TensorFlow/Keras not available - models will not load")
            return

        _patch_legacy_keras_loader(keras_loader)

        # Primary: single fine-tuned model (fast pipeline)
        primary_candidates = [
            'circvis_model.keras',
            'circvis_model_finetune_checkpoint.keras',
            'circvis_model_head_checkpoint.keras',
        ]
        legacy_model_files = {
            'resnet50': ['resnet50.keras', 'resnet50_checkpoint.keras'],
            'mobilenetv2': ['mobilenetv2.keras', 'mobilenetv2_checkpoint.keras'],
            'efficientnetb0': ['efficientnetb0.keras', 'efficientnetb0_checkpoint.keras']
        }

        try:
            keras_loader.utils.generic_utils.get_custom_objects()['BatchNormalization'] = LegacyBatchNormalization
        except Exception:
            pass

        custom_objects = {'BatchNormalization': LegacyBatchNormalization}

        for filename in primary_candidates:
            model_path = self.models_dir / filename
            if not model_path.exists():
                continue
            try:
                self.models['circvis'] = keras_loader.models.load_model(
                    str(model_path),
                    compile=False,
                    custom_objects=custom_objects
                )
                logger.info(f"✓ Loaded primary model from {model_path}")
                break
            except Exception as e:
                self.load_error = f"Model load failed: {e}"
                logger.warning(f"⚠ Could not load primary model from {model_path}: {e}")

        # Fallback: legacy ensemble models
        if not self.models:
            for model_name, candidate_files in legacy_model_files.items():
                for filename in candidate_files:
                    model_path = self.models_dir / filename
                    if not model_path.exists():
                        continue
                    try:
                        self.models[model_name] = keras_loader.models.load_model(
                            str(model_path),
                            compile=False,
                            custom_objects=custom_objects
                        )
                        logger.info(f"✓ Loaded {model_name} from {model_path}")
                        break
                    except Exception as e:
                        logger.warning(f"⚠ Could not load {model_name} from {model_path}: {e}")
        weights_path = self.models_dir / 'ensemble_weights.pkl'
        if weights_path.exists():
            try:
                with open(weights_path, 'rb') as f:
                    self.ensemble_weights = pickle.load(f)
                logger.info(f"✓ Loaded ensemble weights")
            except Exception as e:
                logger.warning(f"⚠ Could not load ensemble weights: {e}")
        
        if not self.models:
            logger.warning("⚠ No models loaded. Run data/train_models.py to train models.")
    
    def predict_single(self, image: np.ndarray, model_name: Optional[str] = None) -> Dict:
        """
        Predict waste class for single image
        
        Args:
            image: numpy array (uint8 0-255 or float 0-1) in RGB format, any shape
            model_name: specific model to use, or ensemble if None
        
        Returns:
            Dictionary with predictions and confidence
        """
        if tf is None and standalone_keras is None:
            raise RuntimeError("TensorFlow or standalone Keras not available")

        if isinstance(image, str):
            image = ImageProcessor.load_image(image)

        # Ensure we have 3D RGB image
        if len(image.shape) == 4 and image.shape[0] == 1:
            image = image[0]
        
        # Convert grayscale to RGB
        if len(image.shape) == 2 or (len(image.shape) == 3 and image.shape[2] == 1):
            if len(image.shape) == 3:
                image = image[:, :, 0]
            image = np.stack([image] * 3, axis=-1)
        
        # Validate image shape
        if len(image.shape) != 3 or image.shape[2] != 3:
            raise ValueError(f"Expected RGB image (H, W, 3), got shape {image.shape}")
        
        # Ensure uint8 for TTA
        if image.dtype != np.uint8:
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)

        start_time = time.time()
        predictions = self._predict_probabilities(image, model_name)
        inference_time = (time.time() - start_time) * 1000

        predictions = apply_calibration(predictions, self.calibration, rgb_image=image)
        return format_prediction(predictions, inference_time)

    def _predict_probabilities(
        self, image: np.ndarray, model_name: Optional[str] = None
    ) -> np.ndarray:
        """
        Run model forward pass with multi-view TTA.
        Image should be uint8 RGB.
        """
        if len(image.shape) == 4:
            image = image[0]

        # Build TTA views (returns uint8 images)
        views = build_tta_views(image)
        
        # Stack views and preprocess (handles uint8 -> normalized float32)
        batch = np.stack(views, axis=0)
        batch = ImageProcessor.preprocess_batch(batch)

        if model_name and model_name in self.models:
            preds = self.models[model_name].predict(batch, verbose=0)
            return np.mean(preds, axis=0)

        if "circvis" in self.models:
            preds = self.models["circvis"].predict(batch, verbose=0)
            return np.mean(preds, axis=0)

        if self.models:
            # Fallback: single view with ensemble
            resized = ImageProcessor.resize_for_model(image)
            batch_single = ImageProcessor.preprocess_batch(np.expand_dims(resized, axis=0))
            return self._ensemble_predict(batch_single)

        raise RuntimeError("No models loaded for inference")
    
    def predict_batch(self, images: List[np.ndarray]) -> List[Dict]:
        """Predict for batch of images"""
        return [self.predict_single(img) for img in images]
    
    def _ensemble_predict(self, images: np.ndarray) -> np.ndarray:
        """
        Ensemble prediction using soft voting
        
        Args:
            images: batch of preprocessed images (N, 224, 224, 3)
        
        Returns:
            Average predictions across models
        """
        predictions = []
        weights = []
        
        for model_name, model in self.models.items():
            pred = model.predict(images, verbose=0)[0]
            predictions.append(pred)
            
            # Use stored weights or uniform
            if self.ensemble_weights and model_name in self.ensemble_weights:
                weights.append(self.ensemble_weights[model_name])
            else:
                weights.append(1.0 / len(self.models))
        
        # Weighted average
        weights = np.array(weights)
        weights = weights / weights.sum()
        ensemble_pred = np.average(predictions, axis=0, weights=weights)
        
        return ensemble_pred
    
    def get_model_stats(self) -> Dict:
        """Get statistics for loaded models"""
        stats = {}
        
        for model_name, model in self.models.items():
            total_params = model.count_params()
            
            # Estimate model size (4 bytes per parameter for float32)
            model_size_mb = (total_params * 4) / (1024 * 1024)
            
            stats[model_name] = {
                'total_parameters': int(total_params),
                'estimated_size_mb': float(model_size_mb),
                'loaded': True
            }
        
        return stats
    
    def is_ready(self) -> bool:
        """Check if models are ready for inference"""
        return len(self.models) > 0
    
    def save_ensemble_weights(self, weights: Dict):
        """Save ensemble weights"""
        weights_path = self.models_dir / 'ensemble_weights.pkl'
        with open(weights_path, 'wb') as f:
            pickle.dump(weights, f)
        self.ensemble_weights = weights
        logger.info(f"✓ Ensemble weights saved to {weights_path}")


class MockModelService:
    """Mock model service for testing without trained models"""
    
    def __init__(self):
        self.class_names = ImageProcessor.CLASS_NAMES
        self.num_classes = len(self.class_names)
    
    def predict_single(self, image: np.ndarray, model_name: Optional[str] = None) -> Dict:
        """Return mock predictions"""
        predictions = np.random.dirichlet(np.ones(self.num_classes))
        class_idx = np.argmax(predictions)
        class_name = ImageProcessor.get_display_class_name(self.class_names[class_idx])

        return {
            'class_name': class_name,
            'confidence': float(predictions[class_idx]),
            'all_classes': {
                ImageProcessor.get_display_class_name(self.class_names[i]): float(predictions[i])
                for i in range(len(self.class_names))
            },
            'processing_time_ms': 50.0
        }
    
    def predict_batch(self, images: List[np.ndarray]) -> List[Dict]:
        """Mock batch predictions"""
        return [self.predict_single(img) for img in images]
    
    def get_model_stats(self) -> Dict:
        """Mock model stats"""
        return {
            'mock_model': {
                'total_parameters': 25000000,
                'estimated_size_mb': 95.0,
                'loaded': False,
                'note': 'Demo mode - train models to get real predictions'
            }
        }
    
    def is_ready(self) -> bool:
        return False
