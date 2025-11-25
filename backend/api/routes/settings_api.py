"""
System Settings API Routes
"""
from fastapi import APIRouter, HTTPException, status, Depends

from database.models import SystemSettings, SettingsUpdate
from database.mongodb import get_settings_collection
from core.security import get_current_user

router = APIRouter()


@router.get("", response_model=SystemSettings)
async def get_settings(current_user: dict = Depends(get_current_user)):
    """Get current system settings"""
    settings_collection = get_settings_collection()
    
    # Get settings (should only be one document)
    settings = await settings_collection.find_one()
    
    if not settings:
        # Create default settings if none exist
        default_settings = SystemSettings()
        await settings_collection.insert_one(default_settings.dict())
        return default_settings
    
    return SystemSettings(**settings)


@router.post("", response_model=SystemSettings)
async def update_settings(
    settings_update: SettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update system settings"""
    settings_collection = get_settings_collection()
    
    # Build update dict
    update_dict = {k: v for k, v in settings_update.dict(exclude_unset=True).items()}
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update settings
    from datetime import datetime
    update_dict["updated_at"] = datetime.utcnow()
    
    result = await settings_collection.update_one(
        {},  # Update the first (and only) document
        {"$set": update_dict},
        upsert=True
    )
    
    # Get updated settings
    settings = await settings_collection.find_one()
    
    return SystemSettings(**settings)


@router.post("/reset")
async def reset_settings(current_user: dict = Depends(get_current_user)):
    """Reset settings to default"""
    settings_collection = get_settings_collection()
    
    # Delete existing settings
    await settings_collection.delete_many({})
    
    # Create default settings
    default_settings = SystemSettings()
    await settings_collection.insert_one(default_settings.dict())
    
    return {
        "message": "Settings reset to default",
        "settings": default_settings
    }

