"""
ML Model Management API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from database.models import FlowFeatures, AnomalyResult
from core.security import get_current_user
from ml.anomaly_detector import AnomalyDetector

router = APIRouter()

# Initialize ML model
detector = AnomalyDetector()


@router.get("/status")
async def get_model_status(current_user: dict = Depends(get_current_user)):
    """Get ML model status and metadata"""
    status = detector.get_status()
    return status


@router.post("/retrain")
async def retrain_model(current_user: dict = Depends(get_current_user)):
    """Trigger model retraining"""
    try:
        result = detector.retrain()
        return {
            "message": "Model retrained successfully",
            "details": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Retraining failed: {str(e)}"
        )


@router.post("/threshold")
async def update_threshold(
    threshold: float,
    current_user: dict = Depends(get_current_user)
):
    """Update anomaly detection threshold"""
    if not 0 <= threshold <= 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Threshold must be between 0 and 1"
        )
    
    detector.update_threshold(threshold)
    
    return {
        "message": "Threshold updated successfully",
        "new_threshold": threshold
    }

