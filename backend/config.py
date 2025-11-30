"""
Configuration settings for HomeGuard backend
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "HomeGuard"
    ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "homeguard"
    DEVICES_FILE_PATH: str | None = None
    ALERTS_FILE_PATH: str | None = None
    DEVICES_FILE_PATH: str | None = None
    
    # ML Model
    MODEL_PATH: str = "./ml_models/isolation_forest.joblib"
    SCALER_PATH: str = "./ml_models/scaler.joblib"
    ANOMALY_THRESHOLD: float = 0.5
    AUTO_BLOCK_ENABLED: bool = False
    
    # Zeek Integration
    ZEEK_LOG_PATH: str = "/var/log/zeek"
    ZEEK_CONN_LOG: str = "conn.log"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Firewall
    NFTABLES_TABLE: str = "homeguard"
    NFTABLES_CHAIN: str = "blocked_devices"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

