"""
Security Alerts & Logs API Routes
Comprehensive security monitoring and audit trails
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime, timedelta
from typing import Optional, List
from bson.objectid import ObjectId

from database.models import SecurityAlert, SecurityAlertResponse, SecurityLog, SecurityLogResponse, SecuritySeverity, SecurityAlertType
from database.mongodb import get_security_alerts_collection, get_security_logs_collection
from core.security import get_current_user

router = APIRouter()


@router.get("/security-alerts", response_model=List[SecurityAlertResponse])
async def get_security_alerts(
    severity: Optional[SecuritySeverity] = Query(None, description="Filter by severity"),
    alert_type: Optional[SecurityAlertType] = Query(None, description="Filter by alert type"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get security alerts with filtering"""
    collection = get_security_alerts_collection()
    
    # Build filter
    filter_dict = {
        "timestamp": {
            "$gte": datetime.utcnow() - timedelta(days=days)
        }
    }
    
    if severity:
        filter_dict["severity"] = severity
    if alert_type:
        filter_dict["alert_type"] = alert_type
    
    # Get alerts sorted by timestamp (newest first)
    alerts = await collection.find(filter_dict).sort("timestamp", -1).limit(limit).to_list(None)
    
    return [
        SecurityAlertResponse(
            _id=str(alert["_id"]),
            **alert
        )
        for alert in alerts
    ]


@router.get("/security-alerts/{alert_id}", response_model=SecurityAlertResponse)
async def get_security_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific security alert"""
    collection = get_security_alerts_collection()
    
    try:
        alert = await collection.find_one({"_id": ObjectId(alert_id)})
    except:
        alert = None
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    return SecurityAlertResponse(
        _id=str(alert["_id"]),
        **alert
    )


@router.put("/security-alerts/{alert_id}/acknowledge", response_model=SecurityAlertResponse)
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Acknowledge/mark security alert as reviewed"""
    collection = get_security_alerts_collection()
    
    try:
        object_id = ObjectId(alert_id)
    except:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid alert ID"
        )
    
    # Update alert
    result = await collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "acknowledged": True,
                "acknowledged_by": current_user["email"],
                "acknowledged_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security alert not found"
        )
    
    # Get updated alert
    alert = await collection.find_one({"_id": object_id})
    
    return SecurityAlertResponse(
        _id=str(alert["_id"]),
        **alert
    )


@router.get("/security-alerts/stats/summary")
async def get_alerts_summary(
    days: int = Query(7, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get security alerts summary statistics"""
    collection = get_security_alerts_collection()
    
    # Get all alerts in timeframe
    alerts = await collection.find({
        "timestamp": {
            "$gte": datetime.utcnow() - timedelta(days=days)
        }
    }).to_list(None)
    
    # Calculate statistics
    severity_counts = {
        "info": 0,
        "warning": 0,
        "critical": 0,
        "emergency": 0
    }
    
    type_counts = {}
    acknowledged_count = 0
    
    for alert in alerts:
        severity_counts[alert.get("severity", "info")] += 1
        alert_type = alert.get("alert_type", "unknown")
        type_counts[alert_type] = type_counts.get(alert_type, 0) + 1
        if alert.get("acknowledged", False):
            acknowledged_count += 1
    
    return {
        "total_alerts": len(alerts),
        "acknowledged": acknowledged_count,
        "unacknowledged": len(alerts) - acknowledged_count,
        "by_severity": severity_counts,
        "by_type": type_counts,
        "timeframe_days": days
    }


@router.post("/security-alerts", response_model=SecurityAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_security_alert(
    alert: SecurityAlert,
    current_user: dict = Depends(get_current_user)
):
    """Create a new security alert"""
    collection = get_security_alerts_collection()
    
    alert_dict = alert.model_dump()
    
    result = await collection.insert_one(alert_dict)
    
    created_alert = await collection.find_one({"_id": result.inserted_id})
    
    return SecurityAlertResponse(
        _id=str(created_alert["_id"]),
        **created_alert
    )


# ============= Security Logs =============

@router.get("/security-logs", response_model=List[SecurityLogResponse])
async def get_security_logs(
    actor: Optional[str] = Query(None, description="Filter by actor email"),
    severity: Optional[SecuritySeverity] = Query(None, description="Filter by severity"),
    days: int = Query(30, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of logs to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get security logs with filtering"""
    collection = get_security_logs_collection()
    
    # Build filter
    filter_dict = {
        "timestamp": {
            "$gte": datetime.utcnow() - timedelta(days=days)
        }
    }
    
    if actor:
        filter_dict["actor"] = actor
    if severity:
        filter_dict["severity"] = severity
    
    # Get logs sorted by timestamp (newest first)
    logs = await collection.find(filter_dict).sort("timestamp", -1).limit(limit).to_list(None)
    
    return [
        SecurityLogResponse(
            _id=str(log["_id"]),
            **log
        )
        for log in logs
    ]


@router.post("/security-logs", response_model=SecurityLogResponse, status_code=status.HTTP_201_CREATED)
async def create_security_log(
    log: SecurityLog,
    current_user: dict = Depends(get_current_user)
):
    """Create a security log entry"""
    collection = get_security_logs_collection()
    
    log_dict = log.model_dump()
    
    result = await collection.insert_one(log_dict)
    
    created_log = await collection.find_one({"_id": result.inserted_id})
    
    return SecurityLogResponse(
        _id=str(created_log["_id"]),
        **created_log
    )


@router.get("/security-logs/stats/summary")
async def get_logs_summary(
    days: int = Query(30, description="Number of days to analyze"),
    current_user: dict = Depends(get_current_user)
):
    """Get security logs summary statistics"""
    collection = get_security_logs_collection()
    
    # Get all logs in timeframe
    logs = await collection.find({
        "timestamp": {
            "$gte": datetime.utcnow() - timedelta(days=days)
        }
    }).to_list(None)
    
    # Calculate statistics
    success_count = sum(1 for log in logs if log.get("status") == "success")
    failure_count = sum(1 for log in logs if log.get("status") == "failure")
    
    actions = {}
    actors = {}
    
    for log in logs:
        action = log.get("action", "unknown")
        actions[action] = actions.get(action, 0) + 1
        
        actor = log.get("actor", "unknown")
        actors[actor] = actors.get(actor, 0) + 1
    
    return {
        "total_actions": len(logs),
        "successful": success_count,
        "failed": failure_count,
        "by_action": actions,
        "by_actor": actors,
        "timeframe_days": days
    }
