"""
Device Management API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
from bson import ObjectId

from database.models import Device, DeviceResponse, DeviceUpdate, DeviceStatus, DeviceControl
from database.mongodb import get_devices_collection
from core.security import get_current_user
from core.websocket_manager import websocket_manager
from core.firewall import FirewallController
from core.permissions import require_admin

router = APIRouter()
firewall = FirewallController()


@router.get("", response_model=List[DeviceResponse])
async def get_devices(current_user: dict = Depends(get_current_user)):
    """Get all devices (accessible to all authenticated users)"""
    devices_collection = get_devices_collection()
    devices = await devices_collection.find().to_list(length=1000)
    
    # Convert ObjectId to string
    for device in devices:
        device["_id"] = str(device["_id"])
    
    return devices


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific device details"""
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


@router.post("/{device_id}/control")
async def control_device(
    device_id: str,
    control: DeviceControl,
    current_user: dict = Depends(require_admin)
):
    """Control device - Start or Stop (Admin only)"""
    devices_collection = get_devices_collection()
    
    # Validate action
    if control.action not in ["start", "stop"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'start' or 'stop'"
        )
    
    # Find device
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
    
    # Update device running status
    is_running = control.action == "start"
    
    await devices_collection.update_one(
        {"_id": device["_id"]},
        {
            "$set": {
                "is_running": is_running,
                "status": DeviceStatus.ACTIVE if is_running else DeviceStatus.IDLE,
                "last_seen": datetime.utcnow()
            }
        }
    )
    
    # Notify via WebSocket
    device["_id"] = str(device["_id"])
    device["is_running"] = is_running
    device["status"] = DeviceStatus.ACTIVE if is_running else DeviceStatus.IDLE
    await websocket_manager.send_device_update(device)
    
    action_text = "started" if is_running else "stopped"
    return {
        "message": f"Device {action_text} successfully",
        "device_id": str(device["_id"]),
        "action": control.action,
        "is_running": is_running,
        "status": device["status"]
    }


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


@router.patch("/{device_id}", response_model=DeviceResponse)
async def update_device(
    device_id: str,
    device_update: DeviceUpdate,
    current_user: dict = Depends(require_admin)
):
    """Update device information (Admin only)"""
    
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
    
    # Build update dictionary
    update_data = {}
    if device_update.hostname is not None:
        update_data["hostname"] = device_update.hostname
    if device_update.device_type is not None:
        update_data["device_type"] = device_update.device_type
    if device_update.status is not None:
        update_data["status"] = device_update.status
    if device_update.is_blocked is not None:
        update_data["is_blocked"] = device_update.is_blocked
    if device_update.is_running is not None:
        update_data["is_running"] = device_update.is_running
    
    update_data["last_seen"] = datetime.utcnow()
    
    # Update device
    await devices_collection.update_one(
        {"_id": device["_id"]},
        {"$set": update_data}
    )
    
    # Get updated device
    updated_device = await devices_collection.find_one({"_id": device["_id"]})
    updated_device["_id"] = str(updated_device["_id"])
    
    return updated_device


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    current_user: dict = Depends(require_admin)
):
    """Delete a device (Admin only)"""
    
    devices_collection = get_devices_collection()
    
    try:
        result = await devices_collection.delete_one({"_id": ObjectId(device_id)})
    except:
        result = await devices_collection.delete_one({
            "$or": [{"ip": device_id}, {"mac": device_id}]
        })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    return {
        "message": "Device deleted successfully",
        "device_id": device_id
    }
