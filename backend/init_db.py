"""
Database initialization script
Creates default admin user and system settings
"""
import asyncio
from datetime import datetime
from database.mongodb import (
    connect_db, 
    get_users_collection, 
    get_settings_collection
)
from core.security import get_password_hash
from database.models import SystemSettings


async def init_admin_user():
    """Create default admin user"""
    users = get_users_collection()
    
    # Check if admin exists
    existing = await users.find_one({"email": "admin@homeguard.local"})
    if not existing:
        await users.insert_one({
            "email": "admin@homeguard.local",
            "password_hash": get_password_hash("admin123"),
            "full_name": "Admin User",
            "role": "admin",
            "is_active": True,
            "phone": "+1-555-0100",
            "organization": "HomeGuard Admin",
            "profile_picture_url": None,
            "preferences": {
                "theme": "light",
                "notifications_enabled": True,
                "language": "en"
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_login": None
        })
        print("✅ Admin user created")
        print("   Email: admin@homeguard.local")
        print("   Password: admin123")
    else:
        print("ℹ️  Admin user already exists")


async def init_system_settings():
    """Create default system settings"""
    settings_collection = get_settings_collection()
    
    existing = await settings_collection.find_one()
    if not existing:
        default_settings = SystemSettings()
        await settings_collection.insert_one(default_settings.model_dump())
        print("✅ Default system settings created")
    else:
        print("ℹ️  System settings already exist")




async def main():
    """Initialize database"""
    print("🚀 Initializing HomeGuard Database...")
    
    # Connect to database
    await connect_db()
    
    # Create admin user (required for authentication)
    await init_admin_user()
    
    # Create system settings (required for app functionality)
    await init_system_settings()
    
    print("\n✅ Database initialization complete!")
    print("ℹ️  Note: Devices and alerts are now read from JSON files")
    print("   (configured via DEVICES_FILE_PATH and ALERTS_FILE_PATH)")


if __name__ == "__main__":
    asyncio.run(main())

