"""
Pydantic models for request/response validation
"""

from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime


class PredictionResult(BaseModel):
    """Single image prediction result"""
    class_name: str
    confidence: float
    all_classes: Dict[str, float]
    processing_time_ms: float


class DashboardStats(BaseModel):
    """Dashboard statistics"""
    total_predictions: int
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: List[List[int]]
    class_distribution: Dict[str, int]
    model_names: List[str]


class SustainabilityImpact(BaseModel):
    """Sustainability metrics"""
    class_name: str
    count: int
    weight_kg: float
    co2_saved_kg: float
    recyclable_percentage: float
    total_impact: Dict[str, float]


class ModelComparison(BaseModel):
    """Model performance comparison"""
    model_name: str
    accuracy: float
    inference_time_ms: float
    parameters: int
    model_size_mb: float


class BatchPredictionRequest(BaseModel):
    """Batch prediction request"""
    image_urls: List[str]


class VideoPredictionRequest(BaseModel):
    """Video prediction request"""
    video_url: str
    fps_sampling: int = 1  # Process every nth frame
