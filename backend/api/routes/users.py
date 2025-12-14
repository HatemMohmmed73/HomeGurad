from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any
from database.mongodb import get_users_collection
from database.models import UserProfile
from core.security import get_current_user
from bson import ObjectId
from datetime import datetime

router = APIRouter()

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    # Ensure _id is string for Pydantic validation
    current_user["id"] = str(current_user["_id"])
    current_user["_id"] = str(current_user["_id"])
    return current_user

@router.patch("/me", response_model=UserProfile)
async def update_current_user_profile(
    profile_update: Dict[str, Any] = Body(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Update current user profile (email, full_name, preferences)
    """
    users_collection = get_users_collection()
    
    # Fields allowed to be updated
    allowed_fields = {"email", "full_name", "phone", "organization", "preferences"}
    
    update_data = {k: v for k, v in profile_update.items() if k in allowed_fields}
    
    if not update_data:
        # If no fields to update, just return current user
        current_user["id"] = str(current_user["_id"])
        current_user["_id"] = str(current_user["_id"])
        return current_user
    
    # If updating preferences, merge with existing
    if "preferences" in update_data:
        current_prefs = current_user.get("preferences", {})
        current_prefs.update(update_data["preferences"])
        update_data["preferences"] = current_prefs
    
    update_data["updated_at"] = datetime.utcnow()
    
    # Perform update
    result = await users_collection.find_one_and_update(
        {"_id": current_user["_id"]},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Fix _id for response model
    result["id"] = str(result["_id"])
    result["_id"] = str(result["_id"])
        
    return result
