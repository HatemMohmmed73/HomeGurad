"""
MongoDB Database Connection and Management
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import settings

# Database instance
client: AsyncIOMotorClient = None
database = None


async def connect_db():
    """Connect to MongoDB"""
    global client, database
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        database = client[settings.DATABASE_NAME]
        # Test connection
        await client.admin.command('ping')
        print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise


async def close_db():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        print("✅ MongoDB connection closed")


def get_database():
    """Get database instance"""
    return database


# Collection helpers
def get_devices_collection():
    """Get devices collection"""
    return database.devices


def get_alerts_collection():
    """Get alerts collection"""
    return database.alerts


def get_users_collection():
    """Get users collection"""
    return database.users


def get_settings_collection():
    """Get settings collection"""
    return database.settings


def get_security_alerts_collection():
    """Get security alerts collection"""
    return database.security_alerts


def get_security_logs_collection():
    """Get security logs collection"""
    return database.security_logs


def get_push_subscriptions_collection():
    """Get push subscriptions collection"""
    return database.push_subscriptions

