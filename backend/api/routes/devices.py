"""
Device Management API Routes
"""
import json
import logging
import os
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
    """Load devices from JSON file and return as dict {ip: device_data}
    
    Both files are keyed by IP address:
    1. devices.json - Device metadata (names, etc.) keyed by IP
    2. active_devices.json - Active/offline status keyed by IP
    """
    path = Path(file_path)
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as file:
            contents = json.load(file)
            
        devices_map = {}
        
        if isinstance(contents, dict):
            for key, record in contents.items():
                if not isinstance(record, dict):
                    continue
                    
                # Both files are keyed by IP, so use the key as IP
                ip = record.get("ip") or key
                record["ip"] = ip  # Ensure IP is set
                devices_map[ip] = record
            
        return devices_map
    except Exception as exc:
        logger.error("Failed to read devices file %s: %s", file_path, exc)
        return {}


def _update_devices_json_file(ip: str, blocked: bool):
    """Update devices.json to set/remove blocked status for a device
    
    Note: This may fail if the file is mounted read-only. That's okay - 
    the firewall state is the source of truth anyway.
    """
    if not settings.DEVICES_METADATA_FILE_PATH:
        return
    
    file_path = Path(settings.DEVICES_METADATA_FILE_PATH)
    if not file_path.exists():
        logger.debug(f"devices.json not found at {file_path}, skipping update")
        return
    
    try:
        # Check if file is writable
        if not os.access(file_path, os.W_OK):
            logger.debug(f"devices.json is read-only, cannot update. Firewall state is source of truth anyway.")
            return
        
        # Read current content
        with file_path.open("r", encoding="utf-8") as file:
            contents = json.load(file)
        
        if not isinstance(contents, dict):
            logger.error("devices.json is not a valid JSON object")
            return
        
        # Find the device entry (keyed by IP)
        device_entry = None
        device_key = None
        
        for key, record in contents.items():
            if isinstance(record, dict) and record.get("ip") == ip:
                device_entry = record
                device_key = key
                break
        
        if device_entry:
            # Update blocked status
            if blocked:
                device_entry["blocked"] = True
                device_entry["status"] = "Blocked"
            else:
                device_entry.pop("blocked", None)  # Remove blocked field
                # Update status to active if it was Blocked
                if device_entry.get("status") == "Blocked":
                    device_entry["status"] = "active"
            
            # Write back to file
            with file_path.open("w", encoding="utf-8") as file:
                json.dump(contents, file, indent=2)
            
            logger.info(f"Updated devices.json: IP {ip} blocked={blocked}")
        else:
            logger.debug(f"Device {ip} not found in devices.json, skipping update")
            
    except PermissionError:
        logger.debug(f"devices.json is read-only, cannot update. Firewall state is source of truth.")
    except Exception as exc:
        logger.warning(f"Failed to update devices.json for {ip}: {exc}")


@router.get("", response_model=List[DeviceResponse])
async def get_devices(current_user: dict = Depends(get_current_user)):
    """
    Get all devices with merged data from DB, active_devices.json, and devices.json.
    - Database is source of truth for USER-ASSIGNED NAMES.
    - active_devices.json determines if device is ACTIVE (present) or OFFLINE (not present).
    - devices.json is source of truth for DEVICE METADATA/NAMES (if not in DB).
    - Status is simplified: ACTIVE (in active_devices.json) or OFFLINE (not in active_devices.json).
    """
    devices_collection = get_devices_collection()
    
    # 1. Fetch all known devices from DB (keyed by IP for matching)
    db_cursor = devices_collection.find()
    db_devices_list = await db_cursor.to_list(length=1000)
    db_devices_map = {d.get("ip"): d for d in db_devices_list if d.get("ip")}
    
    # 2. Fetch active devices (keyed by IP) - if device is here, it's ACTIVE
    active_devices_map = {}
    if settings.DEVICES_FILE_PATH:
        active_devices_map = _load_devices_from_file(settings.DEVICES_FILE_PATH)
    
    # 3. Fetch device metadata/names from devices.json (keyed by IP)
    metadata_devices_map = {}
    if settings.DEVICES_METADATA_FILE_PATH:
        metadata_devices_map = _load_devices_from_file(settings.DEVICES_METADATA_FILE_PATH)
    
    final_devices = []
    
    # 4. Collect all device IPs from all sources (JSON files + DB)
    excluded_ips = {
        "fe80::3e6a:d2ff:fe0d:17fa",  # IPv6 link-local
        "0.0.0.0",  # Invalid/placeholder IP
        "::1",  # IPv6 localhost
        "127.0.0.1",  # IPv4 localhost
        "::",  # Empty/invalid IPv6
        "192.168.100.228",  # External/Unknown device to hide
    }
    
    # Combine IPs from all sources: JSON files and database
    all_device_ips = set(metadata_devices_map.keys()) | set(active_devices_map.keys()) | set(db_devices_map.keys())
    
    # Filter out excluded IPs
    filtered_device_ips = {ip for ip in all_device_ips if ip not in excluded_ips}
    
    for ip in filtered_device_ips:
        metadata_dev = metadata_devices_map.get(ip, {})
        active_dev = active_devices_map.get(ip, {})
        db_dev = db_devices_map.get(ip)
        
        # Determine if device is ACTIVE (in active_devices.json) or OFFLINE (not in active_devices.json)
        is_active = ip in active_devices_map
        
        # Get device name (Priority: devices.json > DB > active_devices.json > "Unknown Device")
        # Always prefer devices.json if it has a name, even if DB has "Unknown Device"
        device_name = None
        if metadata_dev.get("name") and metadata_dev.get("name") != "Unknown Device" and metadata_dev.get("name") != "External/Unknown":
            # Prefer devices.json name if it's a real name
            device_name = metadata_dev.get("name")
        elif db_dev and db_dev.get("hostname") and db_dev.get("hostname") != "Unknown Device":
            # Use DB name if it's not "Unknown Device"
            device_name = db_dev.get("hostname")
        elif metadata_dev.get("name"):
            # Fallback to devices.json even if it's "External/Unknown"
            device_name = metadata_dev.get("name")
        elif active_dev.get("name"):
            device_name = active_dev.get("name")
        
        if not device_name:
            device_name = "Unknown Device"
        
        # Check if device is blocked - use firewall state as source of truth
        # ALWAYS check actual firewall state first (nftables malicious_devices set)
        is_blocked = False
        firewall_check_worked = False
        
        if ip:
            try:
                # Check actual firewall state (nftables)
                is_blocked = firewall.is_ip_blocked_in_firewall(ip)
                firewall_check_worked = True
                logger.info(f"[DEVICE_STATUS] IP: {ip} | Firewall check: {'BLOCKED' if is_blocked else 'NOT BLOCKED'}")
                print(f"[DEVICE_STATUS] IP: {ip} | Firewall: {'🚫 BLOCKED' if is_blocked else '✅ NOT BLOCKED'}", flush=True)
            except Exception as e:
                logger.warning(f"[DEVICE_STATUS] Failed to check firewall state for {ip}: {e}")
                print(f"[DEVICE_STATUS] ⚠️  Firewall check failed for {ip}: {e}", flush=True)
        
        # Only use files/DB as fallback if firewall check completely failed
        # If firewall check worked, trust it (even if it says not blocked)
        if not firewall_check_worked:
            # Firewall check failed - use files/DB as fallback
            is_blocked = (
                metadata_dev.get("blocked", False) or 
                active_dev.get("blocked", False) or 
                (db_dev and db_dev.get("is_blocked", False))
            )
            logger.debug(f"Using fallback check for {ip}: {'BLOCKED' if is_blocked else 'NOT BLOCKED'}")
        
        # Determine status: BLOCKED takes priority, then ACTIVE if in active_devices.json, otherwise OFFLINE
        if is_blocked:
            device_status = DeviceStatus.BLOCKED
        elif is_active:
            device_status = DeviceStatus.ACTIVE
        else:
            device_status = DeviceStatus.OFFLINE
        
        # Get MAC address (from any source)
        mac = None
        if db_dev and db_dev.get("mac"):
            mac = db_dev.get("mac")
        elif metadata_dev.get("mac"):
            mac = metadata_dev.get("mac")
        elif active_dev.get("mac"):
            mac = active_dev.get("mac")
        else:
            # Generate a placeholder MAC if none exists
            mac = f"00:00:00:00:{ip.replace('.', ':')}" if '.' in ip else f"00:00:00:00:00:00"
        
        # Merge metadata
        merged_metadata = {**metadata_dev, **active_dev}
        
        if db_dev:
            # Update existing DB device
            updates = {
                "ip": ip,
                "status": device_status,
                "last_seen": datetime.utcnow(),
                "is_blocked": is_blocked,  # Sync blocked status from files
                "is_running": not is_blocked,  # Update is_running based on blocked status
            }
            
            # Update name from devices.json if it's better than what's in DB
            # Always update if DB has "Unknown Device" or if devices.json has a real name
            db_hostname = db_dev.get("hostname", "")
            should_update_name = (
                not db_hostname or 
                db_hostname == "Unknown Device" or 
                (metadata_dev.get("name") and metadata_dev.get("name") != "Unknown Device" and metadata_dev.get("name") != db_hostname)
            )
            
            if should_update_name and device_name != "Unknown Device":
                updates["hostname"] = device_name
                updates["device_type"] = device_name
                # Also update in memory for response
                db_dev["hostname"] = device_name
                db_dev["device_type"] = device_name
            
            # Update MAC if missing
            if not db_dev.get("mac") and mac:
                updates["mac"] = mac
            
            # Update metadata
            if "metadata" not in db_dev or not db_dev.get("metadata"):
                updates["metadata"] = merged_metadata
            
            # Apply updates
            db_dev.update(updates)
            await devices_collection.update_one({"_id": db_dev["_id"]}, {"$set": updates})
            
            # Prepare response
            db_dev["id"] = str(db_dev["_id"])
            db_dev["_id"] = str(db_dev["_id"])
            db_dev["status"] = device_status  # Ensure status is set correctly
            db_dev["is_blocked"] = is_blocked  # Ensure is_blocked is set correctly
            
            # Ensure default fields
            if "total_bytes_sent" not in db_dev:
                db_dev["total_bytes_sent"] = 0
            if "total_bytes_received" not in db_dev:
                db_dev["total_bytes_received"] = 0
            if "packet_count" not in db_dev:
                db_dev["packet_count"] = 0
            if "is_running" not in db_dev:
                db_dev["is_running"] = not is_blocked
            
            final_devices.append(DeviceResponse(**db_dev))
        else:
            # Create new device in DB
            new_device = {
                "mac": mac,
                "ip": ip,
                "hostname": device_name,
                "device_type": device_name if device_name != "Unknown Device" else "Unknown",
                "status": device_status,
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
                "total_bytes_sent": 0,
                "total_bytes_received": 0,
                "packet_count": 0,
                "is_blocked": is_blocked,  # Use the computed is_blocked value
                "is_running": not is_blocked,
                "metadata": merged_metadata
            }
            
            result = await devices_collection.insert_one(new_device)
            new_device["id"] = str(result.inserted_id)
            new_device["_id"] = str(result.inserted_id)
            
            final_devices.append(DeviceResponse(**new_device))
    
    # 6. Filter out any remaining devices from DB that have excluded IPs
    # (in case they exist in DB but not in the files)
    final_devices = [device for device in final_devices if device.ip not in excluded_ips]
    
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
    
    # Update devices.json to reflect blocked status
    _update_devices_json_file(device["ip"], blocked=True)
    
    # Update device status in DB (for tracking, but firewall is source of truth)
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
        # Check if device is already unblocked in firewall
        if not firewall.is_ip_blocked_in_firewall(device["ip"]):
            # Device is not blocked in firewall, so treat as success
            logger.info(f"Device {device['ip']} is not blocked in firewall, treating unblock as successful")
            success = True
        elif not device.get("is_blocked", False):
            # Device is already unblocked in DB, firewall operation just failed
            logger.info(f"Device {device['ip']} is already unblocked in DB, firewall operation may have failed because IP was not in set")
            success = True
        else:
            # Device is blocked in firewall and DB, but unblock failed
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to unblock device in firewall. The device may not be in the blocked set, or there was an error: {device['ip']}"
            )
    
    # Update devices.json to reflect unblocked status
    if success:
        _update_devices_json_file(device["ip"], blocked=False)
    
    # Update device status in DB (for tracking, but firewall is source of truth)
    if success:
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
