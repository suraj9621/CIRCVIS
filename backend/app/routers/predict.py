"""
Prediction routes for CIRCVIS API
"""

import logging
import io
import numpy as np
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
import cv2
from PIL import Image

from ..models.schemas import PredictionResult
from ..utils.helpers import ImageProcessor
from ..utils.image_loader import load_image_from_upload

logger = logging.getLogger(__name__)
router = APIRouter()


def _log_prediction(request, result, source: str, filename: str = None, source_url: str = None):
    prediction_log = getattr(request.app.state, "prediction_log", None)
    if prediction_log is None:
        return
    try:
        internal_name = ImageProcessor.get_internal_class_name(result.get("class_name", ""))
        prediction_log.log_prediction(
            internal_class_name=internal_name,
            display_class_name=result.get("class_name", internal_name),
            confidence=float(result.get("confidence", 0.0)),
            processing_time_ms=float(result.get("processing_time_ms", 0.0)),
            model_name=result.get("model_name", "circvis"),
            source=source,
            filename=filename,
            source_url=source_url,
        )
    except Exception as exc:
        logger.warning("Prediction log failed: %s", exc)


@router.post("/predict", response_model=PredictionResult)
async def predict_image(request: Request, file: UploadFile = File(...)):
    """
    Single image prediction endpoint
    
    Usage:
        curl -X POST -F "file=@image.jpg" http://localhost:8000/api/predict
    """
    model_service = request.app.state.model_service
    
    if model_service is None:
        raise HTTPException(
            status_code=503,
            detail="Models not loaded. Run training pipeline first."
        )
    
    try:
        contents = await file.read()
        image_array = load_image_from_upload(contents)
        result = model_service.predict_single(image_array)
        _log_prediction(request, result, source="upload", filename=file.filename)
        return PredictionResult(**result)
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict-base64")
async def predict_base64(request: Request, data: dict):
    """
    Predict from base64 encoded image
    
    Body:
        {"image": "base64_string"}
    """
    model_service = request.app.state.model_service
    
    if model_service is None:
        raise HTTPException(status_code=503, detail="Models not loaded.")
    
    try:
        image_array = ImageProcessor.base64_to_array(data.get("image", ""))
        result = model_service.predict_single(image_array)
        _log_prediction(request, result, source="base64")
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"Base64 prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict-batch")
async def predict_batch(request: Request, files: List[UploadFile] = File(...)):
    """
    Batch prediction endpoint
    
    Usage:
        curl -X POST -F "files=@img1.jpg" -F "files=@img2.jpg" http://localhost:8000/api/predict-batch
    """
    model_service = request.app.state.model_service
    
    if model_service is None:
        raise HTTPException(status_code=503, detail="Models not loaded.")
    
    try:
        results = []
        
        for file in files:
            contents = await file.read()
            image_array = load_image_from_upload(contents)
            result = model_service.predict_single(image_array)
            _log_prediction(request, result, source="batch", filename=file.filename)
            results.append({**result, "filename": file.filename})
        
        return JSONResponse({
            "predictions": results,
            "total": len(results)
        })
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/predict-url")
async def predict_url(request: Request, data: dict):
    """
    Predict from image URL
    
    Body:
        {"url": "https://example.com/image.jpg"}
    """
    model_service = request.app.state.model_service
    
    if model_service is None:
        raise HTTPException(status_code=503, detail="Models not loaded.")
    
    try:
        url = data.get("url")
        if not url:
            raise ValueError("Missing 'url' in request body")
        
        # Download image
        import requests
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        image_array = load_image_from_upload(response.content)
        result = model_service.predict_single(image_array)
        _log_prediction(request, result, source="url", source_url=url)
        result['source_url'] = url
        
        return JSONResponse(result)
    
    except Exception as e:
        logger.error(f"URL prediction error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/models")
async def get_models(request: Request):
    """Get list of available models"""
    from ..services.training_stats import build_model_info

    model_service = request.app.state.model_service

    if model_service is None or not model_service.is_ready():
        return JSONResponse({
            "models": [],
            "ready": False,
            "message": "No models loaded. Run: python data/finetune_model.py",
        })

    stats = model_service.get_model_stats()
    info = build_model_info(stats)

    return JSONResponse({
        "models": list(model_service.models.keys()),
        "stats": stats,
        "info": info,
        "ready": model_service.is_ready(),
    })


@router.get("/classes")
async def get_classes():
    """Get list of waste classes"""
    return JSONResponse({
        "classes": [ImageProcessor.get_display_class_name(c) for c in ImageProcessor.CLASS_NAMES],
        "count": len(ImageProcessor.CLASS_NAMES)
    })
