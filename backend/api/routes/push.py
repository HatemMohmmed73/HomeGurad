"""
Push Notification API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime

from database.models import PushSubscriptionCreate
from database.mongodb import get_push_subscriptions_collection
from core.security import get_current_user
from core.push_notifications import push_service

router = APIRouter()


@router.get("/vapid-public-key")
async def get_vapid_public_key(current_user: dict = Depends(get_current_user)):
    """Get VAPID public key for push subscription"""
    return {
        "public_key": push_service.get_vapid_public_key()
    }


@router.post("/subscribe")
async def subscribe_push(
    subscription: PushSubscriptionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Subscribe to push notifications"""
    subscriptions_collection = get_push_subscriptions_collection()
    user_email = current_user["email"]
    
    # Check if subscription already exists
    existing = await subscriptions_collection.find_one({
        "endpoint": subscription.endpoint,
        "user_email": user_email
    })
    
    if existing:
        # Update existing subscription
        await subscriptions_collection.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "keys": subscription.keys,
                    "user_agent": subscription.user_agent,
                    "device_info": subscription.device_info,
                    "last_used": datetime.utcnow(),
                    "is_active": True
                }
            }
        )
        return {"message": "Subscription updated", "subscription_id": str(existing["_id"])}
    else:
        # Create new subscription
        subscription_data = {
            "user_email": user_email,
            "endpoint": subscription.endpoint,
            "keys": subscription.keys,
            "user_agent": subscription.user_agent,
            "device_info": subscription.device_info,
            "created_at": datetime.utcnow(),
            "last_used": datetime.utcnow(),
            "is_active": True
        }
        result = await subscriptions_collection.insert_one(subscription_data)
        return {
            "message": "Subscription created",
            "subscription_id": str(result.inserted_id)
        }


@router.post("/unsubscribe")
async def unsubscribe_push(
    endpoint: str,
    current_user: dict = Depends(get_current_user)
):
    """Unsubscribe from push notifications"""
    subscriptions_collection = get_push_subscriptions_collection()
    user_email = current_user["email"]
    
    result = await subscriptions_collection.update_one(
        {
            "endpoint": endpoint,
            "user_email": user_email
        },
        {
            "$set": {
                "is_active": False
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    
    return {"message": "Unsubscribed successfully"}


@router.get("/subscriptions")
async def get_my_subscriptions(current_user: dict = Depends(get_current_user)):
    """Get all push subscriptions for current user"""
    subscriptions_collection = get_push_subscriptions_collection()
    user_email = current_user["email"]
    
    subscriptions = await subscriptions_collection.find({
        "user_email": user_email,
        "is_active": True
    }).to_list(length=100)
    
    return {
        "subscriptions": [
            {
                "id": str(sub["_id"]),
                "endpoint": sub["endpoint"],
                "user_agent": sub.get("user_agent"),
                "device_info": sub.get("device_info"),
                "created_at": sub.get("created_at").isoformat() if sub.get("created_at") else None,
                "last_used": sub.get("last_used").isoformat() if sub.get("last_used") else None,
            }
            for sub in subscriptions
        ]
    }

