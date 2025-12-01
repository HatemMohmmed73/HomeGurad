"""
Web Push Notification Service
Sends push notifications to all user's registered devices
"""
import json
import logging
from typing import List, Dict, Any
from pywebpush import webpush, WebPushException
from py_vapid import Vapid01
import os

from database.mongodb import get_push_subscriptions_collection
from config import settings

logger = logging.getLogger(__name__)


class PushNotificationService:
    """Service for sending Web Push notifications"""
    
    def __init__(self):
        self.vapid_private_key = None
        self.vapid_public_key = None
        self.vapid_email = "admin@homeguard.local"
        self._load_vapid_keys()
    
    def _load_vapid_keys(self):
        """Load or generate VAPID keys"""
        try:
            # Generate VAPID keys using py-vapid
            vapid = Vapid01()
            vapid.generate_keys()
            
            # Store keys (in production, save these and load from environment)
            self.vapid_private_key = vapid
            self.vapid_public_key = vapid.public_key
            
            logger.info("VAPID keys generated")
            logger.warning("⚠️  For production, save VAPID keys and set VAPID_PRIVATE_KEY environment variable")
        except Exception as e:
            logger.error(f"Error generating VAPID keys: {e}")
    
    def get_vapid_public_key(self) -> str:
        """Get VAPID public key for client subscription in base64url format"""
        if not self.vapid_public_key:
            return ""
        
        try:
            # Convert public key to base64url format
            from cryptography.hazmat.primitives import serialization
            pub_bytes = self.vapid_public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            import base64
            # Remove the first byte (0x04) which indicates uncompressed format
            pub_bytes_no_prefix = pub_bytes[1:]
            return base64.urlsafe_b64encode(pub_bytes_no_prefix).decode('utf-8').rstrip('=')
        except Exception as e:
            logger.error(f"Error encoding VAPID public key: {e}")
            return ""
    
    async def send_to_subscription(self, subscription: Dict[str, Any], payload: Dict[str, Any]) -> bool:
        """Send push notification to a single subscription"""
        try:
            subscription_info = {
                "endpoint": subscription["endpoint"],
                "keys": {
                    "p256dh": subscription["keys"]["p256dh"],
                    "auth": subscription["keys"]["auth"]
                }
            }
            
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=self.vapid_private_key.private_key,
                vapid_claims={
                    "sub": f"mailto:{self.vapid_email}"
                }
            )
            return True
        except WebPushException as e:
            logger.warning(f"WebPush error: {e}")
            # If subscription is invalid, mark as inactive
            if hasattr(e, 'response') and e.response and hasattr(e.response, 'status_code'):
                if e.response.status_code in [410, 404]:
                    return False
            return False
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def send_to_user(self, user_email: str, payload: Dict[str, Any]) -> int:
        """Send push notification to all devices of a user"""
        subscriptions_collection = get_push_subscriptions_collection()
        
        # Get all active subscriptions for user
        subscriptions = await subscriptions_collection.find({
            "user_email": user_email,
            "is_active": True
        }).to_list(length=100)
        
        if not subscriptions:
            logger.info(f"No active subscriptions for user: {user_email}")
            return 0
        
        sent_count = 0
        inactive_subscriptions = []
        
        for sub in subscriptions:
            success = await self.send_to_subscription(sub, payload)
            if success:
                sent_count += 1
                # Update last_used
                await subscriptions_collection.update_one(
                    {"_id": sub["_id"]},
                    {"$set": {"last_used": __import__("datetime").datetime.utcnow()}}
                )
            else:
                # Mark as inactive if failed
                inactive_subscriptions.append(sub["_id"])
        
        # Mark failed subscriptions as inactive
        if inactive_subscriptions:
            await subscriptions_collection.update_many(
                {"_id": {"$in": inactive_subscriptions}},
                {"$set": {"is_active": False}}
            )
        
        logger.info(f"Sent push notifications to {sent_count}/{len(subscriptions)} devices for {user_email}")
        return sent_count
    
    async def send_to_all_users(self, payload: Dict[str, Any]) -> int:
        """Send push notification to all users (for alerts)"""
        subscriptions_collection = get_push_subscriptions_collection()
        
        # Get all active subscriptions
        subscriptions = await subscriptions_collection.find({
            "is_active": True
        }).to_list(length=1000)
        
        if not subscriptions:
            return 0
        
        sent_count = 0
        inactive_subscriptions = []
        
        for sub in subscriptions:
            success = await self.send_to_subscription(sub, payload)
            if success:
                sent_count += 1
                await subscriptions_collection.update_one(
                    {"_id": sub["_id"]},
                    {"$set": {"last_used": __import__("datetime").datetime.utcnow()}}
                )
            else:
                inactive_subscriptions.append(sub["_id"])
        
        if inactive_subscriptions:
            await subscriptions_collection.update_many(
                {"_id": {"$in": inactive_subscriptions}},
                {"$set": {"is_active": False}}
            )
        
        logger.info(f"Sent push notifications to {sent_count}/{len(subscriptions)} devices")
        return sent_count


# Global instance
push_service = PushNotificationService()

