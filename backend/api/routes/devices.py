"""
Device Management API Routes
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, status, Depends

from database.models import (
    DeviceResponse,
    DeviceStatus,
)
from database.mongodb import get_devices_collection
from core.security import get_current_user
from core.websocket_manager import websocket_manager
from core.firewall import FirewallController
from core.permissions import require_admin
from config import settings

router = APIRouter()
firewall = FirewallController()
logger = logging.getLogger(__name__)


def _load_devices_from_file(file_path: str) -> Optional[List[DeviceResponse]]:
    path = Path(file_path)
    if not path.exists():
        logger.warning("Devices file %s not found", file_path)
        return None

    try:
        with path.open("r", encoding="utf-8") as file:
            contents = json.load(file)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Failed to read devices file %s: %s", file_path, exc)
        return None

    devices: List[DeviceResponse] = []

    def to_dt(ts):
        return datetime.fromtimestamp(ts) if isinstance(ts, (int, float)) else datetime.utcnow()

    for ip, record in contents.items():
        blocked = bool(record.get("blocked"))
        status_str = (record.get("status") or "").lower()
        if blocked:
            status = DeviceStatus.BLOCKED
        elif status_str == "normal":
            status = DeviceStatus.ACTIVE
        else:
            status = DeviceStatus.IDLE

        devices.append(
            DeviceResponse(
                _id=ip,
                mac=record.get("mac") or ip,
                ip=ip,
                hostname=record.get("name"),
                device_type=record.get("name") or "Device",
                status=status,
                first_seen=to_dt(record.get("first_seen")),
                last_seen=to_dt(record.get("last_seen")),
                total_bytes_sent=0,
                total_bytes_received=0,
                packet_count=0,
                behavioral_score=0.0,
                is_blocked=blocked,
                is_running=not blocked,
                metadata=record,
            )
        )

    return devices


@router.get("", response_model=List[DeviceResponse])
async def get_devices(current_user: dict = Depends(get_current_user)):
    """Get all devices (accessible to all authenticated users)"""
    if settings.DEVICES_FILE_PATH:
        file_devices = _load_devices_from_file(settings.DEVICES_FILE_PATH)
        if file_devices is not None:
            return file_devices

    devices_collection = get_devices_collection()
    devices = await devices_collection.find().to_list(length=1000)
    
    # Convert ObjectId to string
    for device in devices:
        device["_id"] = str(device["_id"])
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific device details"""

    if settings.DEVICES_FILE_PATH:
        file_devices = _load_devices_from_file(settings.DEVICES_FILE_PATH)
        if file_devices is not None:
            for device in file_devices:
                if device.ip == device_id or device.mac == device_id or str(device._id) == device_id:
                    return device
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Device not found"
            )

    devices_collection = get_devices_collection()
    
    try:
        device = await devices_collection.find_one({"_id": ObjectId(device_id)})
    except:
        # Try by IP or MAC if not ObjectId
        device = await devices_collection.find_one({
            "$or": [{"ip": device_id}, {"mac": device_id}]
        })
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    device["_id"] = str(device["_id"])
    return device


@router.post("/{device_id}/block")
async def block_device(
    device_id: str,
    current_user: dict = Depends(require_admin)
):
    """Block a device (Admin only)"""
    
    devices_collection = get_devices_collection()
    
    try:
        device = await devices_collection.find_one({"_id": ObjectId(device_id)})
    except:
        device = await devices_collection.find_one({
            "$or": [{"ip": device_id}, {"mac": device_id}]
        })
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Block device in firewall
    success = firewall.block_device(device["ip"], device["mac"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to block device in firewall"
        )
    
    # Update device status
    await devices_collection.update_one(
        {"_id": device["_id"]},
        {
            "$set": {
                "is_blocked": True,
                "status": DeviceStatus.BLOCKED,
                "last_seen": datetime.utcnow()
            }
        }
    )
    
    # Notify via WebSocket
    device["_id"] = str(device["_id"])
    device["is_blocked"] = True
    device["status"] = DeviceStatus.BLOCKED
    await websocket_manager.send_device_update(device)
    
    return {
        "message": "Device blocked successfully",
        "device_id": str(device["_id"]),
        "is_blocked": True,
        "status": DeviceStatus.BLOCKED
    }


@router.post("/{device_id}/unblock")
async def unblock_device(
    device_id: str,
    current_user: dict = Depends(require_admin)
):
    """Unblock a device (Admin only)"""
    
    devices_collection = get_devices_collection()
    
    try:
        device = await devices_collection.find_one({"_id": ObjectId(device_id)})
    except:
        device = await devices_collection.find_one({
            "$or": [{"ip": device_id}, {"mac": device_id}]
        })
    
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Unblock device in firewall
    success = firewall.unblock_device(device["ip"], device["mac"])
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unblock device in firewall"
        )
    
    # Update device status
    await devices_collection.update_one(
        {"_id": device["_id"]},
        {
            "$set": {
                "is_blocked": False,
                "status": DeviceStatus.ACTIVE,
                "last_seen": datetime.utcnow()
            }
        }
    )
    
    # Notify via WebSocket
    device["_id"] = str(device["_id"])
    device["is_blocked"] = False
    device["status"] = DeviceStatus.ACTIVE
    await websocket_manager.send_device_update(device)
    
    return {
        "message": "Device unblocked successfully",
        "device_id": str(device["_id"]),
        "is_blocked": False,
        "status": DeviceStatus.ACTIVE
    }


