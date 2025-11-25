"""
Database initialization script
Creates default admin user, system settings, and demo devices
"""
import asyncio
from datetime import datetime, timedelta
from database.mongodb import (
    connect_db, 
    get_users_collection, 
    get_settings_collection,
    get_devices_collection,
    get_security_alerts_collection
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


async def init_demo_devices():
    """Create demo devices for testing"""
    devices_collection = get_devices_collection()
    
    # Check if demo devices exist
    existing_count = await devices_collection.count_documents({})
    if existing_count == 0:
        demo_devices = [
            {
                "mac": "00:11:22:33:44:55",
                "ip": "192.168.1.100",
                "hostname": "smart-tv-living-room",
                "device_type": "Smart TV",
                "status": "active",
                "first_seen": datetime.utcnow() - timedelta(days=30),
                "last_seen": datetime.utcnow() - timedelta(seconds=5),
                "total_bytes_sent": 1024000,
                "total_bytes_received": 5120000,
                "packet_count": 12500,
                "behavioral_score": 0.15,  # Low anomaly score
                "is_blocked": False,
                "metadata": {
                    "brand": "Samsung",
                    "model": "UE55RU8000",
                    "os": "Tizen",
                    "last_update": "2025-01-15"
                }
            },
            {
                "mac": "AA:BB:CC:DD:EE:FF",
                "ip": "192.168.1.101",
                "hostname": "smart-camera-bedroom",
                "device_type": "Security Camera",
                "status": "active",
                "first_seen": datetime.utcnow() - timedelta(days=20),
                "last_seen": datetime.utcnow() - timedelta(seconds=10),
                "total_bytes_sent": 512000,
                "total_bytes_received": 256000,
                "packet_count": 8900,
                "behavioral_score": 0.05,  # Very low anomaly score
                "is_blocked": False,
                "metadata": {
                    "brand": "Logitech",
                    "model": "Circle View",
                    "resolution": "1080p",
                    "powered_by": "battery"
                }
            },
            {
                "mac": "11:22:33:44:55:66",
                "ip": "192.168.1.102",
                "hostname": "smart-thermostat",
                "device_type": "Thermostat",
                "status": "idle",
                "first_seen": datetime.utcnow() - timedelta(days=60),
                "last_seen": datetime.utcnow() - timedelta(minutes=5),
                "total_bytes_sent": 102400,
                "total_bytes_received": 204800,
                "packet_count": 3200,
                "behavioral_score": 0.08,
                "is_blocked": False,
                "metadata": {
                    "brand": "Nest",
                    "model": "Learning Thermostat",
                    "temperature_unit": "celsius"
                }
            },
            {
                "mac": "22:33:44:55:66:77",
                "ip": "192.168.1.103",
                "hostname": "smart-doorbell",
                "device_type": "Smart Doorbell",
                "status": "active",
                "first_seen": datetime.utcnow() - timedelta(days=15),
                "last_seen": datetime.utcnow() - timedelta(seconds=30),
                "total_bytes_sent": 256000,
                "total_bytes_received": 1024000,
                "packet_count": 5600,
                "behavioral_score": 0.25,  # Slightly higher anomaly score
                "is_blocked": False,
                "metadata": {
                    "brand": "Ring",
                    "model": "Video Doorbell Pro",
                    "wifi_strength": "-45dBm",
                    "firmware": "1.18.43"
                }
            },
            {
                "mac": "33:44:55:66:77:88",
                "ip": "192.168.1.104",
                "hostname": "smart-light-kitchen",
                "device_type": "Smart Light",
                "status": "active",
                "first_seen": datetime.utcnow() - timedelta(days=45),
                "last_seen": datetime.utcnow() - timedelta(seconds=15),
                "total_bytes_sent": 51200,
                "total_bytes_received": 102400,
                "packet_count": 2100,
                "behavioral_score": 0.02,  # Very low anomaly
                "is_blocked": False,
                "metadata": {
                    "brand": "Philips Hue",
                    "model": "White Ambiance",
                    "color_temp_range": "2000K-6500K"
                }
            },
            {
                "mac": "44:55:66:77:88:99",
                "ip": "192.168.1.200",
                "hostname": "suspicious-device",
                "device_type": "Unknown",
                "status": "active",
                "first_seen": datetime.utcnow() - timedelta(days=2),
                "last_seen": datetime.utcnow() - timedelta(seconds=2),
                "total_bytes_sent": 10240000,
                "total_bytes_received": 2048000,
                "packet_count": 150000,
                "behavioral_score": 0.87,  # HIGH ANOMALY SCORE - Demo for alerts!
                "is_blocked": False,
                "metadata": {
                    "brand": "Unknown",
                    "model": "Unknown",
                    "note": "Suspicious behavior - for demo/testing"
                }
            }
        ]
        
        result = await devices_collection.insert_many(demo_devices)
        print(f"✅ {len(result.inserted_ids)} demo devices created")
        print("   - smart-tv-living-room (Normal)")
        print("   - smart-camera-bedroom (Normal)")
        print("   - smart-thermostat (Idle)")
        print("   - smart-doorbell (Normal)")
        print("   - smart-light-kitchen (Normal)")
        print("   - suspicious-device (HIGH ANOMALY - for testing alerts!)")
    else:
        print(f"ℹ️  Demo devices already exist ({existing_count} devices)")


async def init_security_alerts():
    """Create default security alerts for testing"""
    alerts_collection = get_security_alerts_collection()
    
    # Check if alerts exist
    existing_count = await alerts_collection.count_documents({})
    if existing_count == 0:
        default_alerts = [
            {
                "alert_type": "anomaly_detected",
                "device_mac": "00:11:22:33:44:55",
                "device_ip": "192.168.1.100",
                "device_name": "smart-tv-living-room",
                "severity": "high",
                "message": "Anomalous activity detected on smart TV.",
                "details": {
                    "anomaly_type": "unusual_network_traffic",
                    "anomaly_score": 0.95,
                    "timestamp": datetime.utcnow() - timedelta(minutes=10)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=10),
                "updated_at": datetime.utcnow() - timedelta(minutes=10)
            },
            {
                "alert_type": "suspicious_login",
                "device_mac": "AA:BB:CC:DD:EE:FF",
                "device_ip": "192.168.1.101",
                "device_name": "smart-camera-bedroom",
                "severity": "medium",
                "message": "Suspicious login attempt from a new location.",
                "details": {
                    "ip_address": "192.168.1.101",
                    "timestamp": datetime.utcnow() - timedelta(minutes=5)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=5),
                "updated_at": datetime.utcnow() - timedelta(minutes=5)
            },
            {
                "alert_type": "unauthorized_access",
                "device_mac": "11:22:33:44:55:66",
                "device_ip": "192.168.1.102",
                "device_name": "smart-thermostat",
                "severity": "low",
                "message": "Unauthorized access to thermostat settings.",
                "details": {
                    "action": "change_temperature",
                    "target_temperature": 75,
                    "timestamp": datetime.utcnow() - timedelta(minutes=2)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=2),
                "updated_at": datetime.utcnow() - timedelta(minutes=2)
            },
            {
                "alert_type": "network_outage",
                "device_mac": "22:33:44:55:66:77",
                "device_ip": "192.168.1.103",
                "device_name": "smart-doorbell",
                "severity": "critical",
                "message": "Network outage detected for smart doorbell.",
                "details": {
                    "duration": "15 minutes",
                    "timestamp": datetime.utcnow() - timedelta(minutes=15)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=15),
                "updated_at": datetime.utcnow() - timedelta(minutes=15)
            },
            {
                "alert_type": "anomaly_detected",
                "device_mac": "33:44:55:66:77:88",
                "device_ip": "192.168.1.104",
                "device_name": "smart-light-kitchen",
                "severity": "high",
                "message": "Anomalous activity detected on smart light.",
                "details": {
                    "anomaly_type": "unusual_power_consumption",
                    "anomaly_score": 0.90,
                    "timestamp": datetime.utcnow() - timedelta(minutes=3)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=3),
                "updated_at": datetime.utcnow() - timedelta(minutes=3)
            },
            {
                "alert_type": "suspicious_device",
                "device_mac": "44:55:66:77:88:99",
                "device_ip": "192.168.1.200",
                "device_name": "suspicious-device",
                "severity": "critical",
                "message": "Suspicious device activity detected.",
                "details": {
                    "anomaly_type": "unknown_device_behavior",
                    "anomaly_score": 0.99,
                    "timestamp": datetime.utcnow() - timedelta(minutes=1)
                },
                "status": "acknowledged",
                "assigned_to": "admin@homeguard.local",
                "created_at": datetime.utcnow() - timedelta(minutes=1),
                "updated_at": datetime.utcnow() - timedelta(minutes=1)
            }
        ]
        
        result = await alerts_collection.insert_many(default_alerts)
        print(f"✅ {len(result.inserted_ids)} security alerts created")
        print("   - Anomaly on smart-tv-living-room (High)")
        print("   - Suspicious login on smart-camera-bedroom (Medium)")
        print("   - Unauthorized access on smart-thermostat (Low)")
        print("   - Network outage on smart-doorbell (Critical)")
        print("   - Anomaly on smart-light-kitchen (High)")
        print("   - Suspicious device on suspicious-device (Critical)")
    else:
        print(f"ℹ️  Security alerts already exist ({existing_count} alerts)")


async def main():
    """Initialize database"""
    print("🚀 Initializing HomeGuard Database...")
    
    # Connect to database
    await connect_db()
    
    # Create admin user
    await init_admin_user()
    
    # Create system settings
    await init_system_settings()
    
    # Create demo devices
    await init_demo_devices()

    # Create security alerts
    await init_security_alerts()
    
    print("\n✅ Database initialization complete!")


if __name__ == "__main__":
    asyncio.run(main())

