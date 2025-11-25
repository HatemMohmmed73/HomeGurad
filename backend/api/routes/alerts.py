"""
Alerts API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, timedelta

from database.models import Alert, AlertResponse, AlertSeverity, AlertType
from database.mongodb import get_alerts_collection
from core.security import get_current_user

router = APIRouter()


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[AlertSeverity] = None,
    device_id: Optional[str] = None,
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get all alerts with optional filters"""
    alerts_collection = get_alerts_collection()
    
    # Build query
    query = {}
    
    # Time filter
    if days > 0:
        start_date = datetime.utcnow() - timedelta(days=days)
        query["timestamp"] = {"$gte": start_date}
    
    # Severity filter
    if severity:
        query["severity"] = severity
    
    # Device filter
    if device_id:
        query["device_id"] = device_id
    
    # Fetch alerts
    alerts = await alerts_collection.find(query).sort("timestamp", -1).limit(limit).to_list(length=limit)
    
    # Convert ObjectId to string
    for alert in alerts:
        alert["_id"] = str(alert["_id"])
    
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific alert details"""
    alerts_collection = get_alerts_collection()
    
    from bson import ObjectId
    try:
        alert = await alerts_collection.find_one({"_id": ObjectId(alert_id)})
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID"
        )
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    alert["_id"] = str(alert["_id"])
    return alert


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an alert as acknowledged"""
    alerts_collection = get_alerts_collection()
    
    from bson import ObjectId
    try:
        obj_id = ObjectId(alert_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID"
        )
    
    result = await alerts_collection.update_one(
        {"_id": obj_id},
        {"$set": {"acknowledged": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert acknowledged successfully"}


@router.get("/stats/summary")
async def get_alert_stats(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get alert statistics"""
    alerts_collection = get_alerts_collection()
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total alerts
    total_alerts = await alerts_collection.count_documents({
        "timestamp": {"$gte": start_date}
    })
    
    # Alerts by severity
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$severity",
            "count": {"$sum": 1}
        }}
    ]
    severity_stats = await alerts_collection.aggregate(pipeline).to_list(length=10)
    
    # Alerts by type
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$alert_type",
            "count": {"$sum": 1}
        }}
    ]
    type_stats = await alerts_collection.aggregate(pipeline).to_list(length=10)
    
    # Alerts by device
    pipeline = [
        {"$match": {"timestamp": {"$gte": start_date}}},
        {"$group": {
            "_id": "$device_ip",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    device_stats = await alerts_collection.aggregate(pipeline).to_list(length=10)
    
    return {
        "total_alerts": total_alerts,
        "by_severity": {item["_id"]: item["count"] for item in severity_stats},
        "by_type": {item["_id"]: item["count"] for item in type_stats},
        "top_devices": device_stats,
        "period_days": days
    }


@router.delete("/{alert_id}")
async def delete_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Delete an alert"""
    alerts_collection = get_alerts_collection()
    
    from bson import ObjectId
    try:
        obj_id = ObjectId(alert_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID"
        )
    
    result = await alerts_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return {"message": "Alert deleted successfully"}

