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
from database.mongodb import get_users_collection
from config import settings

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitors alerts.json file for new alerts and sends WebSocket notifications"""
    
    def __init__(self):
        self.last_alert_ids: Set[str] = set()
        self.monitoring = False
        self.file_path: Optional[Path] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start monitoring alerts file"""
        try:
            if not settings.ALERTS_FILE_PATH:
                logger.warning("ALERTS_FILE_PATH not configured, alert monitoring disabled")
                print("⚠️  Alert monitoring disabled: ALERTS_FILE_PATH not configured")
                return
            
            self.file_path = Path(settings.ALERTS_FILE_PATH)
            if not self.file_path.exists():
                logger.warning(f"Alerts file not found: {self.file_path}")
                print(f"⚠️  Alert monitoring disabled: alerts file not found at {self.file_path}")
                return
            
            self.monitoring = True
            # Load initial alerts
            self._load_initial_alerts()
            # Start monitoring task - store it to prevent garbage collection
            self._monitor_task = asyncio.create_task(self._monitor_loop())
            logger.info(f"Alert monitoring started for {self.file_path}")
            print(f"✅ Alert monitoring started for {self.file_path}")
        except Exception as e:
            logger.error(f"Error starting alert monitor: {e}", exc_info=True)
            # Don't crash the app if monitoring fails to start
            print(f"⚠️  Alert monitoring failed to start: {e}")
    
    def _load_initial_alerts(self):
        """Load existing alerts to track which ones are new"""
        try:
            if self.file_path and self.file_path.exists():
                with open(self.file_path, 'r') as f:
                    alerts = json.load(f)
                    if isinstance(alerts, list):
                        self.last_alert_ids = {alert.get("alert_id") for alert in alerts if alert.get("alert_id")}
        except Exception as e:
            logger.error(f"Error loading initial alerts: {e}")
    
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
            # Get file modification time
            mtime = self.file_path.stat().st_mtime
            
            # Read alerts
            with open(self.file_path, 'r') as f:
                alerts = json.load(f)
            
            if not isinstance(alerts, list):
                return
            
            # Find new alerts
            current_alert_ids = {alert.get("alert_id") for alert in alerts if alert.get("alert_id")}
            new_alert_ids = current_alert_ids - self.last_alert_ids
            
            if new_alert_ids:
                # Send notifications for new alerts
                for alert in alerts:
                    alert_id = alert.get("alert_id")
                    if alert_id in new_alert_ids:
                        await self._send_alert_notification(alert)
                
                # Update tracked alert IDs
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
            
            # 1. Send via WebSocket (Popups)
            await websocket_manager.send_alert(alert_payload)
            logger.info(f"Sent WebSocket notification for alert: {alert_payload.get('alert_id')}")
            
            # 2. Send via Email
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
