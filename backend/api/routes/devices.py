"""
Device Management API Routes
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

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
from config import settings

router = APIRouter()
firewall = FirewallController()
logger = logging.getLogger(__name__)


def _load_devices_from_file(file_path: str) -> Dict[str, dict]:
    """Load devices from JSON file and return as dict {mac: device_data}"""
    path = Path(file_path)
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            contents = json.load(file)
            
        devices_map = {}
        for ip, record in contents.items():
            mac = record.get("mac")
            if not mac:
                continue
                
            # Normalize record
            record["ip"] = ip
            devices_map[mac] = record
            
        return devices_map
    except Exception as exc:
        logger.error("Failed to read devices file %s: %s", file_path, exc)
        return {}


@router.get("", response_model=List[DeviceResponse])
async def get_devices(current_user: dict = Depends(get_current_user)):
    """
    Get all devices with merged status from DB and JSON file.
    - Database is source of truth for NAMES.
    - JSON file is source of truth for ACTIVITY.
    """
    devices_collection = get_devices_collection()
    
    # 1. Fetch all known devices from DB
    db_cursor = devices_collection.find()
    db_devices_list = await db_cursor.to_list(length=1000)
    db_devices_map = {d.get("mac"): d for d in db_devices_list if d.get("mac")}
    
    # 2. Fetch current active devices from JSON
    json_devices_map = {}
    if settings.DEVICES_FILE_PATH:
        json_devices_map = _load_devices_from_file(settings.DEVICES_FILE_PATH)
    
    final_devices = []
    
    # 3. Process DB devices (Registered devices)
    for mac, db_dev in db_devices_map.items():
        json_dev = json_devices_map.get(mac)
        
        if json_dev:
            # Device is ACTIVE (found in JSON)
            # Update DB record with latest info from JSON, but KEEP DB Name
            updates = {
                "ip": json_dev.get("ip"),
                "status": DeviceStatus.ACTIVE if not db_dev.get("is_blocked") else DeviceStatus.BLOCKED,
                "last_seen": datetime.utcnow(),
                # Don't update hostname if DB has one!
            }
            
            # Sync metadata if needed
            if "metadata" not in db_dev:
                updates["metadata"] = json_dev
                
            # Apply updates to DB object in memory
            db_dev.update(updates)
            
            # Persist activity update to DB
            await devices_collection.update_one({"_id": db_dev["_id"]}, {"$set": updates})
            
            # Remove from json_map so we don't process it again
            del json_devices_map[mac]
            
        else:
            # Device is INACTIVE (Not in JSON)
            # Mark as Offline/Idle if not already
            if db_dev.get("status") not in [DeviceStatus.OFFLINE, DeviceStatus.BLOCKED]:
                db_dev["status"] = DeviceStatus.OFFLINE
                # Update DB
                await devices_collection.update_one(
                    {"_id": db_dev["_id"]}, 
                    {"$set": {"status": DeviceStatus.OFFLINE}}
                )
        
        # Add to result
        db_dev["id"] = str(db_dev["_id"])
        db_dev["_id"] = str(db_dev["_id"])
        
        # Ensure default fields are present for Pydantic validation if missing in DB
        if "total_bytes_sent" not in db_dev:
            db_dev["total_bytes_sent"] = 0
        if "total_bytes_received" not in db_dev:
            db_dev["total_bytes_received"] = 0
        if "packet_count" not in db_dev:
            db_dev["packet_count"] = 0
        if "is_running" not in db_dev:
            db_dev["is_running"] = not db_dev.get("is_blocked", False)

        final_devices.append(DeviceResponse(**db_dev))
        
    # 4. Process Remaining JSON devices (New/Unknown devices)
    for mac, json_dev in json_devices_map.items():
        # Determine initial name
        initial_name = json_dev.get("name")
        device_type = "Unknown"
        
        if not initial_name:
            initial_name = "Unknown Device"
        else:
            device_type = initial_name # Guess type from name
            
        new_device = {
            "mac": mac,
            "ip": json_dev.get("ip"),
            "hostname": initial_name,
            "device_type": device_type,
            "status": DeviceStatus.ACTIVE,
            "first_seen": datetime.utcnow(),
            "last_seen": datetime.utcnow(),
            "total_bytes_sent": 0,
            "total_bytes_received": 0,
            "packet_count": 0,
            "is_blocked": bool(json_dev.get("blocked", False)),
            "is_running": not bool(json_dev.get("blocked", False)),
            "metadata": json_dev
        }
        
        # Insert into DB immediately so it's "Known" (but maybe unnamed)
        result = await devices_collection.insert_one(new_device)
        new_device["id"] = str(result.inserted_id)
        new_device["_id"] = str(result.inserted_id)
        
        final_devices.append(DeviceResponse(**new_device))
        
    return final_devices


@router.post("/{device_id}/name")
async def update_device_name(
    device_id: str, 
    name: str,
    current_user: dict = Depends(get_current_user)
):
    """Update device name/hostname"""
    
    devices_collection = get_devices_collection()
    
    try:
        device = await devices_collection.find_one({"_id": ObjectId(device_id)})
    except:
        device = await devices_collection.find_one({
            "$or": [{"ip": device_id}, {"mac": device_id}]
        })
    
    if not device:
        # Check if it's in the JSON file but not DB
        if settings.DEVICES_FILE_PATH:
            json_map = _load_devices_from_file(settings.DEVICES_FILE_PATH)
            # Find by IP or MAC
            found_json = None
            found_mac = None
            
            for mac, record in json_map.items():
                if record["ip"] == device_id or mac == device_id:
                    found_json = record
                    found_mac = mac
                    break
            
            if found_json:
                # Create DB record now
                new_device = {
                    "mac": found_mac,
                    "ip": found_json.get("ip"),
                    "hostname": name,  # Set the NEW name
                    "device_type": name,
                    "status": DeviceStatus.ACTIVE,
                    "first_seen": datetime.utcnow(),
                    "last_seen": datetime.utcnow(),
                    "total_bytes_sent": 0,
                    "total_bytes_received": 0,
                    "packet_count": 0,
                    "is_blocked": False,
                    "is_running": True,
                    "metadata": found_json
                }
                result = await devices_collection.insert_one(new_device)
                new_device["id"] = str(result.inserted_id)
                new_device["_id"] = str(result.inserted_id)
                return new_device

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    # Normal Update
    await devices_collection.update_one(
        {"_id": device["_id"]},
        {"$set": {"hostname": name, "device_type": name}}
    )
    
    # Return updated device
    device["hostname"] = name
    device["device_type"] = name
    device["_id"] = str(device["_id"])
    device["id"] = str(device["_id"])
    
    # Ensure missing fields for response
    if "total_bytes_sent" not in device:
        device["total_bytes_sent"] = 0
    if "total_bytes_received" not in device:
        device["total_bytes_received"] = 0
    if "packet_count" not in device:
        device["packet_count"] = 0
    if "is_running" not in device:
        device["is_running"] = not device.get("is_blocked", False)
    
    return device


@router.get("/{device_id}", response_model=DeviceResponse)
async def get_device(device_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific device details"""
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
    
    device["_id"] = str(device["_id"])
    device["id"] = str(device["_id"])
    
    # Ensure missing fields for response
    if "total_bytes_sent" not in device:
        device["total_bytes_sent"] = 0
    if "total_bytes_received" not in device:
        device["total_bytes_received"] = 0
    if "packet_count" not in device:
        device["packet_count"] = 0
    if "is_running" not in device:
        device["is_running"] = not device.get("is_blocked", False)

    return device


@router.post("/{device_id}/block")
async def block_device(
    device_id: str, 
    current_user: dict = Depends(get_current_user)
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
        # Proceed anyway to update DB status? Or fail?
        # Let's log warning and proceed for DB consistency
        logger.warning(f"Firewall block command failed for {device['ip']}")
    
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
    current_user: dict = Depends(get_current_user)
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
        logger.warning(f"Firewall unblock command failed for {device['ip']}")
    
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
