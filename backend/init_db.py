"""
Database initialization script
Creates default admin user and system settings
"""
import asyncio
from datetime import datetime
from database.mongodb import (
    connect_db, 
    get_users_collection, 
)
from core.security import get_password_hash


async def init_admin_user():
    """Create default admin user"""
    users = get_users_collection()
    
    # Check if admin exists by username or email
    existing = await users.find_one({"username": "admin"})
    if not existing:
        # Check if legacy email user exists and update
        legacy = await users.find_one({"email": "admin@homeguard.local"})
        if legacy and "username" not in legacy:
            await users.update_one(
                {"_id": legacy["_id"]},
                {"$set": {"username": "admin"}}
            )
            print("✅ Updated legacy admin user with username='admin'")
        elif not legacy:
            await users.insert_one({
                "username": "admin",
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
            print("   Username: admin")
            print("   Password: admin123")
    else:
        print("ℹ️  Admin user already exists")


async def main():
    """Initialize database"""
    print("🚀 Initializing HomeGuard Database...")
    
    # Connect to database
    await connect_db()
    
    # Create admin user (required for authentication)
    await init_admin_user()
    
    print("\n✅ Database initialization complete!")
    print("ℹ️  Note: Devices and alerts are now read from JSON files")
    print("   (configured via DEVICES_FILE_PATH and ALERTS_FILE_PATH)")


if __name__ == "__main__":
    asyncio.run(main())
