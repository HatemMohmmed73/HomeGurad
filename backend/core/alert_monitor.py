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
from core.push_notifications import push_service
from config import settings

logger = logging.getLogger(__name__)


class AlertMonitor:
    """Monitors alerts.json file for new alerts and sends WebSocket notifications"""
    
    def __init__(self):
        self.last_alert_ids: Set[str] = set()
        self.monitoring = False
        self.file_path: Optional[Path] = None
        
    def start(self):
        """Start monitoring alerts file"""
        if not settings.ALERTS_FILE_PATH:
            logger.warning("ALERTS_FILE_PATH not configured, alert monitoring disabled")
            return
        
        self.file_path = Path(settings.ALERTS_FILE_PATH)
        if not self.file_path.exists():
            logger.warning(f"Alerts file not found: {self.file_path}")
            return
        
        self.monitoring = True
        # Load initial alerts
        self._load_initial_alerts()
        # Start monitoring task
        asyncio.create_task(self._monitor_loop())
        logger.info(f"Alert monitoring started for {self.file_path}")
    
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
        
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON in alerts file: {self.file_path}")
        except Exception as e:
            logger.error(f"Error checking for new alerts: {e}")
    
    async def _send_alert_notification(self, alert_data: dict):
        """Send alert notification via WebSocket and Push"""
        try:
            # Format alert for WebSocket
            device = alert_data.get("device", {})
            alert_payload = {
                "alert_id": alert_data.get("alert_id"),
                "device_ip": device.get("ip", "unknown"),
                "device_name": device.get("name", "Unknown Device"),
                "severity": alert_data.get("severity", "low"),
                "reason": alert_data.get("reason", "Anomalous activity detected"),
                "anomaly_score": alert_data.get("anomaly_score", 0.0),
                "timestamp": alert_data.get("timestamp"),
                "action_taken": alert_data.get("action_taken"),
                "status": alert_data.get("status", "active")
            }
            
            # Send via WebSocket (for active dashboard connections)
            await websocket_manager.send_alert(alert_payload)
            logger.info(f"Sent WebSocket notification for alert: {alert_payload.get('alert_id')}")
            
            # Send via Push Notification (for all registered devices, even when browser is closed)
            push_payload = {
                "title": f"🚨 {alert_payload['severity'].upper()} Alert: {alert_payload['device_name']}",
                "body": alert_payload['reason'],
                "icon": "/favicon.ico",
                "badge": "/favicon.ico",
                "tag": alert_payload['alert_id'],
                "data": {
                    "url": "/alerts",
                    "alert_id": alert_payload['alert_id'],
                    "device_ip": alert_payload['device_ip']
                },
                "requireInteraction": alert_payload['severity'] in ['high', 'critical']
            }
            
            # Send to all users (since we only have one admin user)
            sent_count = await push_service.send_to_all_users(push_payload)
            logger.info(f"Sent push notifications to {sent_count} device(s) for alert: {alert_payload.get('alert_id')}")
        
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")


# Global instance
alert_monitor = AlertMonitor()

