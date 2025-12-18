"""
Alerts API Routes
"""
import json
import logging
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query

from database.models import AlertResponse, AlertSeverity, AlertType
from database.mongodb import get_alerts_collection
from core.security import get_current_user
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _parse_timestamp(value):
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value)
    if isinstance(value, str):
        try:
            # Try ISO format first
            return datetime.fromisoformat(value)
        except ValueError:
            try:
                # Try "YYYY-MM-DD HH:MM:SS" format
                return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                logger.warning("Could not parse timestamp: %s, using current time", value)
                return datetime.utcnow()
    return datetime.utcnow()


def _parse_severity(value: Optional[str]) -> AlertSeverity:
    try:
        return AlertSeverity((value or "low").lower())
    except ValueError:
        return AlertSeverity.LOW


def _load_alerts_from_file(file_path: str) -> Optional[List[AlertResponse]]:
    path = Path(file_path)
    if not path.exists():
        logger.warning("Alerts file %s not found", file_path)
        return None

    try:
        # Try to parse as JSON first (array or single object)
        try:
            raw_data = json.loads(path.read_text(encoding="utf-8"))
            # Handle both single object and array formats
            if isinstance(raw_data, dict):
                raw_alerts = [raw_data]
            elif isinstance(raw_data, list):
                raw_alerts = raw_data
            else:
                logger.error("Alerts file must contain a JSON object or array, got %s", type(raw_data))
                return None
        except json.JSONDecodeError:
            # If JSON parsing fails, try JSONL format (one JSON object per line)
            logger.info("Trying JSONL format (one JSON object per line)")
            raw_alerts = []
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:  # Skip empty lines
                        continue
                    try:
                        alert_obj = json.loads(line)
                        raw_alerts.append(alert_obj)
                    except json.JSONDecodeError:
                        logger.warning("Skipping invalid JSON on line %d", line_num)
                        continue
            
            if not raw_alerts:
                logger.error("No valid alerts found in JSONL format")
                return None
    except Exception as exc:  # pragma: no cover
        logger.error("Failed to read alerts file %s: %s", file_path, exc)
        return None

    results: List[AlertResponse] = []
    for record in raw_alerts:
        device = record.get("device", {})
        ip = device.get("ip") or "unknown"

        results.append(
            AlertResponse(
                _id=record.get("alert_id") or ip,
                device_id=ip,
                device_ip=ip,
                device_mac=device.get("mac") or ip,
                alert_type=AlertType.ANOMALY,
                severity=_parse_severity(record.get("severity")),
                anomaly_score=float(record.get("anomaly_score") or 0.0),
                timestamp=_parse_timestamp(record.get("timestamp")),
                reason=record.get("reason") or "Anomalous activity detected",
                details={
                    "device_name": device.get("name"),
                    "action_taken": record.get("action") or record.get("action_taken"),
                    "status": record.get("status"),
                },
                action_taken=json.dumps(record.get("action") or record.get("action_taken"))
                if (record.get("action") or record.get("action_taken"))
                else None,
                acknowledged=str(record.get("status") or "").lower() == "acknowledged",
            )
        )

    return results


def _filter_file_alerts(
    severity: Optional[AlertSeverity],
    device_id: Optional[str],
    days: int,
    limit: int,
) -> Optional[List[AlertResponse]]:
    alerts = _load_alerts_from_file(settings.ALERTS_FILE_PATH)
    if alerts is None:
        return None

    start_date = datetime.utcnow() - timedelta(days=days) if days > 0 else None
    filtered: List[AlertResponse] = []
    for alert in alerts:
        if severity and alert.severity != severity:
            continue
        if device_id and alert.device_ip != device_id and alert.device_id != device_id:
            continue
        if start_date and alert.timestamp < start_date:
            continue
        filtered.append(alert)

    filtered.sort(key=lambda a: a.timestamp, reverse=True)
    return filtered[:limit]


def _file_alert_stats(days: int):
    alerts = _load_alerts_from_file(settings.ALERTS_FILE_PATH)
    if alerts is None:
        return None

    start_date = datetime.utcnow() - timedelta(days=days) if days > 0 else None
    filtered = [
        alert for alert in alerts
        if start_date is None or alert.timestamp >= start_date
    ]

    total_alerts = len(filtered)
    severity_counts = Counter(alert.severity.value for alert in filtered)
    type_counts = Counter(alert.alert_type.value for alert in filtered)
    device_counts = Counter(alert.device_ip for alert in filtered)
    top_devices = [{"_id": device, "count": count} for device, count in device_counts.most_common(10)]

    return {
        "total_alerts": total_alerts,
        "by_severity": dict(severity_counts),
        "by_type": dict(type_counts),
        "top_devices": top_devices,
        "period_days": days,
    }


@router.get("", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[AlertSeverity] = None,
    device_id: Optional[str] = None,
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(100, description="Maximum number of alerts to return"),
    current_user: dict = Depends(get_current_user)
):
    """Get all alerts with optional filters"""
    # Note: We now sync file alerts to MongoDB in alert_monitor.py, so we ALWAYS read from DB
    # to support features like 'acknowledged' status.
    
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
    
    # Fallback: If MongoDB is empty, try loading from file
    if not alerts and settings.ALERTS_FILE_PATH:
        logger.warning("MongoDB alerts collection is empty, falling back to file-based alerts")
        file_alerts = _filter_file_alerts(severity, device_id, days, limit)
        if file_alerts:
            # Convert AlertResponse objects to dicts for return
            alerts = [alert.dict() for alert in file_alerts]
            logger.info(f"Loaded {len(alerts)} alerts from file as fallback")
    
    # Normalize severity values and convert ObjectId to string
    for alert in alerts:
        # Normalize severity to lowercase (fixes "High" -> "high")
        if "severity" in alert:
            alert["severity"] = _parse_severity(alert["severity"]).value
        
        # Convert ObjectId to string
        if isinstance(alert.get("_id"), dict) or (hasattr(alert.get("_id"), "__str__") and not isinstance(alert.get("_id"), str)):
            alert["_id"] = str(alert["_id"])
    
    return alerts


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, current_user: dict = Depends(get_current_user)):
    """Mark an alert as acknowledged"""
    # File-backed mode support removed (now synced to DB)

    alerts_collection = get_alerts_collection()
    
    from bson import ObjectId
    query_id = alert_id
    try:
        if ObjectId.is_valid(alert_id):
            query_id = ObjectId(alert_id)
    except:
        pass # Keep as string if not valid ObjectId
    
    result = await alerts_collection.update_one(
        {"_id": query_id},
        {"$set": {"acknowledged": True}}
    )
    
    if result.matched_count == 0:
        # Try the other type if first attempt failed (e.g. string vs ObjectId mismatch)
        alt_id = ObjectId(alert_id) if not isinstance(query_id, ObjectId) and ObjectId.is_valid(alert_id) else alert_id
        if alt_id != query_id:
             result = await alerts_collection.update_one(
                {"_id": alt_id},
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
    # Always use MongoDB stats
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



