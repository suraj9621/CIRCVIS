"""
CIRCVIS: Context-Aware Waste Classification FastAPI Backend
Serves ML models and frontend SPA
"""

import os
import logging
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routers import predict, dashboard
from .services.model_service import ModelService, MockModelService
from .services.prediction_log import PredictionLog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
MODEL_FILE = PROJECT_ROOT / "models" / "circvis_model.keras"

# Initialize FastAPI app
app = FastAPI(
    title="CIRCVIS API",
    description="Context-Aware Waste Classification",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Model Service
try:
    logger.info("Initializing Model Service...")
    model_service = ModelService(models_dir=str(PROJECT_ROOT / "models"))
    if model_service.is_ready():
        app.state.model_service = model_service
        logger.info("✓ Model Service initialized successfully")
    elif MODEL_FILE.exists():
        app.state.model_service = model_service
        logger.error("Model file exists but could not load: %s", model_service.load_error)
    else:
        logger.warning("No trained model — using MockModelService")
        app.state.model_service = MockModelService()
except Exception as e:
    logger.warning("⚠ Model service init failed: %s", e)
    app.state.model_service = MockModelService() if MODEL_FILE.exists() else None

try:
    app.state.prediction_log = PredictionLog(PROJECT_ROOT / "data" / "predictions.db")
    app.state.prediction_log.seed_demo_data()
    logger.info("✓ Prediction log initialized at %s", app.state.prediction_log.db_path)
except Exception as e:
    logger.warning("⚠ Prediction log init failed: %s", e)
    app.state.prediction_log = None

# Include routers
app.include_router(predict.router, prefix="/api", tags=["Prediction"])
app.include_router(dashboard.router, prefix="/api", tags=["Dashboard"])

# Mount static files if frontend exists
if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="static")
    logger.info(f"✓ Static files mounted at /assets from {FRONTEND_DIR / 'assets'}")
else:
    logger.warning(f"⚠ Frontend directory not found at {FRONTEND_DIR}")

# Health check (must be before catch-all page route)
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    service = app.state.model_service
    ready = service is not None and hasattr(service, "is_ready") and service.is_ready()
    model_names = list(service.models.keys()) if ready and hasattr(service, "models") else []
    load_error = getattr(service, "load_error", None) if service else "Server not initialized"
    model_file_exists = MODEL_FILE.exists()
    from .services.inference import INFERENCE_VERSION

    return {
        "status": "ok" if ready else "degraded",
        "models_loaded": ready,
        "model_names": model_names,
        "model_file_exists": model_file_exists,
        "load_error": load_error if not ready else None,
        "inference_version": INFERENCE_VERSION,
        "api": "/api/predict",
    }

# Root endpoint - serve index.html
@app.get("/")
async def read_root():
    """Serve landing page"""
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "CIRCVIS API v1.0 - Frontend not found"}

# Serve HTML pages (SPA routing)
@app.get("/{page}")
async def serve_page(page: str):
    """Serve specific HTML pages"""
    if page in {"health", "api"}:
        raise HTTPException(status_code=404, detail="Not found")
    # Support both /demo and /demo.html style URLs
    if page.endswith('.html'):
        page_path = FRONTEND_DIR / page
    else:
        page_path = FRONTEND_DIR / f"{page}.html"

    if page_path.exists():
        return FileResponse(str(page_path))
    raise HTTPException(status_code=404, detail="Page not found")

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("🚀 CIRCVIS API Starting...")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("🛑 CIRCVIS API Shutting down...")

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
