"""
Configuration settings for HomeGuard backend
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "HomeGuard"
    ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str = "dev-secret-key-change-in-production"  # Default for development, MUST be set in production
    ALGORITHM: str = "HS256"
    # Keep admin dashboard sessions stable (avoids WebSocket 403/401 after short expiry)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "homeguard"
    DEVICES_FILE_PATH: str | None = "/data/active_devices.json"  # Real-time device status (from monitor_network.py)
    DEVICES_METADATA_FILE_PATH: str | None = "/data/devices.json"  # Device metadata/names
    ALERTS_FILE_PATH: str | None = "/data/alerts.json"  # Alerts file
    
    # Zeek Integration
    ZEEK_LOG_PATH: str = "/var/log/zeek"
    ZEEK_CONN_LOG: str = "conn.log"
    
    # Frontend
    FRONTEND_URL: str = "http://192.168.100.119/"
    CORS_ORIGINS: List[str] = ["http://192.168.100.119/"]
    
    # Firewall
    NFTABLES_TABLE: str = "homeguard"
    NFTABLES_CHAIN: str = "blocked_devices"

    # Email Settings
    EMAIL_HOST: str = "smtp.gmail.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: str = "noreply@homeguard.local"
    EMAIL_ENABLED: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Warn if using default secret key in production
        if self.SECRET_KEY == "dev-secret-key-change-in-production" and self.ENV == "production":
            import warnings
            warnings.warn(
                "⚠️  WARNING: Using default SECRET_KEY in production! This is a security risk. "
                "Please set SECRET_KEY environment variable.",
                UserWarning
            )


settings = Settings()
