"""
Alert File Monitor - Watches alerts.json for new alerts and sends WebSocket notifications
"""
import asyncio
import json
import logging
from pathlib import Path
from typing import Set, Optional
from datetime import datetime

from core.websocket_manager import websocket_manager
from core.email import email_service
from database.mongodb import get_users_collection, get_alerts_collection
from database.models import AlertSeverity, AlertType
from config import settings

logger = logging.getLogger(__name__)


def _normalize_severity(severity: str) -> str:
    """Normalize severity string to valid enum value"""
    if not severity:
        return "low"
    severity_lower = str(severity).lower()
    # Map common variations to valid enum values
    severity_map = {
        "low": "low",
        "medium": "medium",
        "med": "medium",
        "high": "high",
        "critical": "critical",
        "crit": "critical",
    }
    return severity_map.get(severity_lower, "low")


class AlertMonitor:
    """Monitors alerts.json file for new alerts and sends WebSocket notifications"""
    
    def __init__(self):
        self.last_alert_ids: Set[str] = set()  # Track alert_id:device_ip combinations
        self.monitoring = False
        self.file_path: Optional[Path] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start monitoring alerts file"""
        import sys
        try:
            print(f"🔍 Starting alert monitor... ALERTS_FILE_PATH={settings.ALERTS_FILE_PATH}", flush=True)
            sys.stdout.flush()
            logger.info(f"Starting alert monitor with ALERTS_FILE_PATH={settings.ALERTS_FILE_PATH}")
            
            if not settings.ALERTS_FILE_PATH:
                logger.warning("ALERTS_FILE_PATH not configured, alert monitoring disabled")
                print("⚠️  Alert monitoring disabled: ALERTS_FILE_PATH not configured", flush=True)
                sys.stdout.flush()
                return
            
            self.file_path = Path(settings.ALERTS_FILE_PATH)
            print(f"🔍 Checking for alerts file at: {self.file_path}", flush=True)
            print(f"🔍 File exists: {self.file_path.exists()}", flush=True)
            sys.stdout.flush()
            
            if not self.file_path.exists():
                logger.warning(f"Alerts file not found: {self.file_path}")
                print(f"⚠️  Alert monitoring disabled: alerts file not found at {self.file_path}", flush=True)
                print(f"🔍 Current working directory: {Path.cwd()}", flush=True)
                data_dir = Path('/data')
                if data_dir.exists():
                    print(f"🔍 /data directory contents: {list(data_dir.iterdir())}", flush=True)
                else:
                    print(f"🔍 /data directory does not exist", flush=True)
                sys.stdout.flush()
                return
            
            self.monitoring = True
            print(f"📋 Loading initial alerts from {self.file_path}...", flush=True)
            sys.stdout.flush()
            # Load initial alerts AND sync to DB
            await self._load_initial_alerts()
            # Start monitoring task - store it to prevent garbage collection
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"Alert monitoring started for {self.file_path}")
            print(f"✅ Alert monitoring started for {self.file_path}", flush=True)
            sys.stdout.flush()
        except Exception as e:
            logger.error(f"Error starting alert monitor: {e}", exc_info=True)
            # Don't crash the app if monitoring fails to start
            print(f"⚠️  Alert monitoring failed to start: {e}", flush=True)
            import traceback
            traceback.print_exc()
            sys.stdout.flush()
    
    def _parse_timestamp(self, value):
        """Parse timestamp from various formats"""
        if isinstance(value, (int, float)):
            try:
                return datetime.fromtimestamp(value)
            except (ValueError, OSError) as e:
                logger.warning(f"Invalid timestamp value {value}: {e}, using current time")
                return datetime.utcnow()
        elif isinstance(value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(value)
            except ValueError:
                try:
                    # Try "YYYY-MM-DD HH:MM:SS" format
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    logger.warning(f"Could not parse timestamp string: {value}, using current time")
                    return datetime.utcnow()
        return datetime.utcnow()

    async def _load_initial_alerts(self):
        """Load existing alerts from file and sync to MongoDB"""
        try:
            if not self.file_path or not self.file_path.exists():
                logger.warning(f"Alerts file not found: {self.file_path}")
                print(f"⚠️  Alerts file not found: {self.file_path}")
                return
            
            # Try to read as JSON first (array or single object)
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    
                # Handle both array and single object formats
                if isinstance(data, dict):
                    # Single alert object - convert to array
                    alerts = [data]
                    logger.info("Converted single alert object to array format")
                    print("ℹ️  Converted single alert object to array format")
                elif isinstance(data, list):
                    alerts = data
                else:
                    logger.warning(f"Alerts file has unsupported format. Got type: {type(data)}")
                    print(f"⚠️  Alerts file must be an array or object. Current format: {type(data).__name__}")
                    return
            except json.JSONDecodeError as e:
                # If JSON parsing fails, try JSONL format (one JSON object per line)
                logger.info(f"JSON parsing failed, trying JSONL format: {e}")
                print(f"ℹ️  Trying JSONL format (one JSON object per line)...")
                alerts = []
                with open(self.file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:  # Skip empty lines
                            continue
                        try:
                            alert_obj = json.loads(line)
                            alerts.append(alert_obj)
                        except json.JSONDecodeError as line_error:
                            logger.warning(f"Skipping invalid JSON on line {line_num}: {line_error}")
                            print(f"⚠️  Skipping invalid JSON on line {line_num}")
                
                if not alerts:
                    logger.error("No valid alerts found in JSONL format")
                    print("❌ No valid alerts found in JSONL format")
                    return
                
                logger.info(f"Successfully loaded {len(alerts)} alerts from JSONL format")
                print(f"✅ Loaded {len(alerts)} alerts from JSONL format")

            alerts_collection = get_alerts_collection()
            count = 0
            errors = 0
            skipped = 0
            
            logger.info(f"Processing {len(alerts)} alerts from file")
            print(f"📋 Processing {len(alerts)} alerts from file...")
            
            for alert_data in alerts:
                alert_id = alert_data.get("alert_id")
                if not alert_id:
                    skipped += 1
                    logger.warning("Skipping alert without alert_id")
                    continue
                    
                # Track unique ID (alert_id:device_ip)
                device = alert_data.get("device", {})
                device_ip = device.get("ip", "unknown")
                unique_id = f"{alert_id}:{device_ip}"
                self.last_alert_ids.add(unique_id)
                
                # Sync to MongoDB if missing
                try:
                    device = alert_data.get("device", {})
                    device_ip = device.get("ip", "unknown")
                    
                    # Create unique ID by combining alert_id and device_ip
                    # This handles cases where same alert_id is used for different devices
                    unique_id = f"{alert_id}:{device_ip}"
                    
                    existing = await alerts_collection.find_one({"_id": unique_id})
                    if existing:
                        skipped += 1
                        continue
                    
                    timestamp = self._parse_timestamp(alert_data.get("timestamp"))
                    
                    db_alert = {
                        "_id": unique_id,
                        "alert_id": alert_id,  # Keep original alert_id for reference
                        "device_id": device_ip,
                        "device_ip": device_ip,
                        "device_mac": device.get("mac", "unknown"),
                        "alert_type": "anomaly",
                        "severity": _normalize_severity(alert_data.get("severity")),
                        "timestamp": timestamp,
                        "reason": alert_data.get("reason", "Suspicious activity"),
                        "details": {
                            "device_name": device.get("name"),
                            "status": alert_data.get("status")
                        },
                        "action_taken": json.dumps(alert_data.get("action_taken")) if alert_data.get("action_taken") else None,
                        "acknowledged": False
                    }
                    await alerts_collection.insert_one(db_alert)
                    count += 1
                except Exception as e:
                    errors += 1
                    logger.error(f"Error syncing initial alert {alert_id}: {e}", exc_info=True)
                    print(f"❌ Error syncing alert {alert_id}: {e}")
            
            logger.info(f"Alert sync complete: {count} synced, {skipped} skipped, {errors} errors")
            if count > 0:
                print(f"✅ Synced {count} existing alerts to MongoDB")
            if errors > 0:
                print(f"⚠️  {errors} alerts failed to sync (check logs for details)")
            if skipped > 0:
                print(f"ℹ️  {skipped} alerts already existed in MongoDB")
                    
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in alerts file: {e}", exc_info=True)
            print(f"❌ Invalid JSON in alerts file: {e}")
        except Exception as e:
            logger.error(f"Error loading initial alerts: {e}", exc_info=True)
            print(f"❌ Error loading initial alerts: {e}")
            import traceback
            traceback.print_exc()
    
    async def _monitor_loop(self):
        """Main monitoring loop - checks file every 2 seconds"""
        while self.monitoring:
            try:
                await self._check_for_new_alerts()
                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error in alert monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait longer on error
    
    async def _check_for_new_alerts(self):
        """Check for new alerts in the file"""
        if not self.file_path or not self.file_path.exists():
            return
        
        try:
            # Try to read as JSON first (array or single object)
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                
                # Handle both array and single object formats
                if isinstance(data, dict):
                    # Single alert object - convert to array
                    alerts = [data]
                elif isinstance(data, list):
                    alerts = data
                else:
                    logger.warning(f"Alerts file has unsupported format. Got type: {type(data)}")
                    return
            except json.JSONDecodeError:
                # If JSON parsing fails, try JSONL format (one JSON object per line)
                alerts = []
                with open(self.file_path, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:  # Skip empty lines
                            continue
                        try:
                            alert_obj = json.loads(line)
                            alerts.append(alert_obj)
                        except json.JSONDecodeError:
                            logger.warning(f"Skipping invalid JSON on line {line_num}")
                            continue
                
                if not alerts:
                    logger.warning("No valid alerts found in JSONL format")
                    return
            
            # Find new alerts (by comparing alert_id:device_ip combinations)
            current_alert_ids = set()
            for alert in alerts:
                alert_id = alert.get("alert_id")
                if alert_id:
                    device = alert.get("device", {})
                    device_ip = device.get("ip", "unknown")
                    unique_id = f"{alert_id}:{device_ip}"
                    current_alert_ids.add(unique_id)
            
            new_alert_ids = current_alert_ids - self.last_alert_ids
            
            # Process all alerts: sync to MongoDB and send notifications for new ones
            alerts_collection = get_alerts_collection()
            synced_count = 0
            notified_count = 0
            
            for alert in alerts:
                alert_id = alert.get("alert_id")
                if not alert_id:
                    continue
                
                device = alert.get("device", {})
                device_ip = device.get("ip", "unknown")
                unique_id = f"{alert_id}:{device_ip}"
                
                try:
                    # Always check if alert exists in MongoDB
                    existing = await alerts_collection.find_one({"_id": unique_id})
                    
                    if not existing:
                        # Alert exists in file but not in DB - sync it
                        timestamp = self._parse_timestamp(alert.get("timestamp"))
                        db_alert = {
                            "_id": unique_id,
                            "alert_id": alert_id,  # Keep original alert_id for reference
                            "device_id": device_ip,
                            "device_ip": device_ip,
                            "device_mac": device.get("mac", "unknown"),
                            "alert_type": "anomaly",
                            "severity": _normalize_severity(alert.get("severity")),
                            "timestamp": timestamp,
                            "reason": alert.get("reason", "Suspicious activity"),
                            "details": {
                                "device_name": device.get("name"),
                                "status": alert.get("status")
                            },
                            "action_taken": json.dumps(alert.get("action_taken")) if alert.get("action_taken") else None,
                            "acknowledged": False
                        }
                        await alerts_collection.insert_one(db_alert)
                        synced_count += 1
                        logger.info(f"Synced alert {unique_id} to MongoDB")
                        print(f"✅ Synced alert {unique_id} to MongoDB", flush=True)
                    
                    # If it's a new alert (not in last_alert_ids), send notification
                    if unique_id in new_alert_ids:
                        await self._send_alert_notification(alert)
                        notified_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing alert {unique_id}: {e}", exc_info=True)
                    print(f"❌ Error processing alert {unique_id}: {e}", flush=True)
            
            if synced_count > 0:
                logger.info(f"Synced {synced_count} alert(s) to MongoDB")
                print(f"📋 Synced {synced_count} alert(s) to MongoDB", flush=True)
            
            # Update tracked alert IDs
            if new_alert_ids:
                self.last_alert_ids = current_alert_ids
                logger.info(f"Detected {len(new_alert_ids)} new alert(s)")
                print(f"🚨 Detected {len(new_alert_ids)} new alert(s)")
        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in alerts file: {self.file_path}")
        except Exception as e:
            logger.error(f"Error checking for new alerts: {e}")
    
    async def _send_alert_notification(self, alert_data: dict):
        """Send alert notification via WebSocket and Email"""
        try:
            # Format alert payload
            device = alert_data.get("device", {})
            alert_payload = {
                "alert_id": alert_data.get("alert_id"),
                "device_ip": device.get("ip", "unknown"),
                "device_name": device.get("name", "Unknown Device"),
                "severity": alert_data.get("severity", "low"),
                "reason": alert_data.get("reason", "Suspicious activity detected"),
                "timestamp": alert_data.get("timestamp"),
                "action_taken": alert_data.get("action_taken"),
                "status": alert_data.get("status", "active")
            }
            
            # 1. Persist to MongoDB
            try:
                alerts_collection = get_alerts_collection()
                
                # Create unique ID by combining alert_id and device_ip
                # This handles cases where same alert_id is used for different devices
                unique_id = f"{alert_payload['alert_id']}:{alert_payload['device_ip']}"
                
                # Check if already exists
                existing = await alerts_collection.find_one({"_id": unique_id})
                if not existing:
                    # Prepare document for MongoDB
                    db_alert = {
                        "_id": unique_id,
                        "alert_id": alert_payload["alert_id"],  # Keep original alert_id for reference
                        "device_id": alert_payload["device_ip"], # Use IP as ID fallback
                        "device_ip": alert_payload["device_ip"],
                        "device_mac": device.get("mac", "unknown"),
                        "alert_type": "anomaly", # Default type
                        "severity": _normalize_severity(alert_payload["severity"]),
                        "timestamp": self._parse_timestamp(alert_payload["timestamp"]),
                        "reason": alert_payload["reason"],
                        "details": {
                            "device_name": alert_payload["device_name"],
                            "status": alert_payload["status"]
                        },
                        "action_taken": json.dumps(alert_payload["action_taken"]) if alert_payload["action_taken"] else None,
                        "acknowledged": False
                    }
                    await alerts_collection.insert_one(db_alert)
                    logger.info(f"Persisted alert {unique_id} to MongoDB")
            except Exception as e:
                logger.error(f"Error persisting alert to MongoDB: {e}")

            # 2. Send via WebSocket (Popups)
            await websocket_manager.send_alert(alert_payload)
            logger.info(f"Sent WebSocket notification for alert: {alert_payload.get('alert_id')}")
            
            # 3. Send via Email
            try:
                users_collection = get_users_collection()
                # Find admins who have notifications enabled
                async for user in users_collection.find({
                    "role": "admin",
                    "preferences.notifications_enabled": True
                }):
                    if user.get("email"):
                        logger.info(f"Sending email alert to {user['email']}")
                        print(f"📧 Sending email alert to {user['email']}")
                        ok = email_service.send_alert_email(user["email"], alert_payload)
                        print(f"📧 Email send result to {user['email']}: {ok}")
            except Exception as e:
                logger.error(f"Error sending email notifications: {e}")
                print(f"⚠️  Error while sending email notifications: {e}")
        
        except Exception as e:
            logger.error(f"Error processing alert notification: {e}")


# Global instance
alert_monitor = AlertMonitor()
