"""
Database Models (Pydantic Schemas)
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============= Enum Definitions =============

class DeviceStatus(str, Enum):
    """Device connection status"""
    ACTIVE = "active"
    IDLE = "idle"
    BLOCKED = "blocked"
    OFFLINE = "offline"


class AlertSeverity(str, Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(str, Enum):
    """Types of alerts"""
    PORT_SCAN = "port_scan"
    FLOOD = "flood"
    DATA_EXFILTRATION = "data_exfiltration"
    UNUSUAL_TRAFFIC = "unusual_traffic"
    UNKNOWN_DESTINATION = "unknown_destination"
    ANOMALY = "anomaly"


class UserRole(str, Enum):
    """Single admin role for the system"""
    ADMIN = "admin"


# ============= Device Models =============

class Device(BaseModel):
    """IoT Device Model"""
    mac: str = Field(..., description="MAC address")
    ip: str = Field(..., description="IP address")
    hostname: Optional[str] = Field(None, description="Device hostname")
    device_type: Optional[str] = Field("unknown", description="Device type")
    status: DeviceStatus = Field(DeviceStatus.IDLE, description="Device status")
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    total_bytes_sent: int = Field(0, description="Total bytes sent")
    total_bytes_received: int = Field(0, description="Total bytes received")
    packet_count: int = Field(0, description="Total packet count")
    behavioral_score: float = Field(0.0, description="Anomaly score (0-1)")
    is_blocked: bool = Field(False, description="Is device blocked")
    is_running: bool = Field(True, description="Is device running")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DeviceResponse(Device):
    """Device response with ID"""
    _id: str = Field(..., description="Device ID")

    class Config:
        populate_by_name = True


class DeviceUpdate(BaseModel):
    """Device update model"""
    hostname: Optional[str] = None
    device_type: Optional[str] = None
    status: Optional[DeviceStatus] = None
    is_blocked: Optional[bool] = None
    is_running: Optional[bool] = None


class DeviceControl(BaseModel):
    """Device control model for start/stop operations"""
    action: str = Field(..., description="Action: 'start' or 'stop'")


# ============= Alert Models =============

class Alert(BaseModel):
    """Alert Model"""
    device_id: str = Field(..., description="Device ID")
    device_ip: str = Field(..., description="Device IP")
    device_mac: str = Field(..., description="Device MAC")
    alert_type: AlertType = Field(..., description="Type of alert")
    severity: AlertSeverity = Field(..., description="Severity level")
    anomaly_score: float = Field(..., description="Anomaly score from ML")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reason: str = Field(..., description="Human-readable explanation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")
    action_taken: Optional[str] = Field(None, description="Action taken (blocked, alerted)")
    acknowledged: bool = Field(False, description="Whether alert has been reviewed")


class AlertResponse(Alert):
    """Alert response with ID"""
    id: str = Field(..., alias="_id")

    class Config:
        populate_by_name = True


# ============= User Models =============

class User(BaseModel):
    """Admin user record"""
    email: str = Field(..., description="User email")
    password_hash: str = Field(..., description="Hashed password")
    full_name: Optional[str] = Field(None, description="Full name")
    role: str = Field(UserRole.ADMIN, description="User role")
    is_active: bool = Field(True, description="Account active status")
    phone: Optional[str] = Field(None, description="Phone number")
    organization: Optional[str] = Field(None, description="Organization/Home name")
    profile_picture_url: Optional[str] = Field(None, description="Profile picture URL")
    preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "theme": "light",
            "notifications_enabled": True,
            "language": "en"
        },
        description="User preferences"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")


class UserProfile(BaseModel):
    """User profile response"""
    id: str = Field(..., alias="_id")
    email: str
    full_name: Optional[str]
    role: str
    phone: Optional[str]
    organization: Optional[str]
    profile_picture_url: Optional[str]
    preferences: Dict[str, Any]
    created_at: Optional[datetime] = None
    last_login: Optional[datetime]
    
    class Config:
        populate_by_name = True


class UserLogin(BaseModel):
    """User login model with validation"""
    email: str = Field(..., min_length=5, description="User email")
    password: str = Field(..., min_length=1, description="Password")


class Token(BaseModel):
    """JWT Token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    email: Optional[str] = None


# ============= Push Notification Models =============

class PushSubscription(BaseModel):
    """Web Push Subscription Model"""
    user_email: str = Field(..., description="User email who owns this subscription")
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: Dict[str, str] = Field(..., description="Encryption keys (p256dh, auth)")
    user_agent: Optional[str] = Field(None, description="Browser user agent")
    device_info: Optional[Dict[str, Any]] = Field(None, description="Device information")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(True, description="Is subscription active")


class PushSubscriptionCreate(BaseModel):
    """Push subscription creation model"""
    endpoint: str = Field(..., description="Push service endpoint URL")
    keys: Dict[str, str] = Field(..., description="Encryption keys")
    user_agent: Optional[str] = None
    device_info: Optional[Dict[str, Any]] = None


# ============= Settings Models =============

class SystemSettings(BaseModel):
    """System configuration settings"""
    auto_block_enabled: bool = Field(False, description="Auto-block on anomaly")
    anomaly_threshold: float = Field(0.5, description="ML anomaly threshold")
    alert_notification_enabled: bool = Field(True, description="Enable notifications")
    model_retrain_interval_hours: int = Field(24, description="Model retrain interval")
    zeek_monitoring_enabled: bool = Field(True, description="Zeek monitoring status")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SettingsUpdate(BaseModel):
    """Settings update model"""
    auto_block_enabled: Optional[bool] = None
    anomaly_threshold: Optional[float] = None
    alert_notification_enabled: Optional[bool] = None
    model_retrain_interval_hours: Optional[int] = None
    zeek_monitoring_enabled: Optional[bool] = None


# ============= ML Models =============

class FlowFeatures(BaseModel):
    """Network flow features for ML inference"""
    duration: float = Field(..., description="Flow duration in seconds")
    orig_bytes: int = Field(..., description="Bytes from originator")
    resp_bytes: int = Field(..., description="Bytes from responder")
    orig_pkts: int = Field(..., description="Packets from originator")
    resp_pkts: int = Field(..., description="Packets from responder")
    orig_ip_bytes: int = Field(..., description="IP bytes from originator")
    resp_ip_bytes: int = Field(..., description="IP bytes from responder")
    port: int = Field(..., description="Destination port")
    protocol: str = Field(..., description="Protocol (tcp, udp, icmp)")


class AnomalyResult(BaseModel):
    """ML model inference result"""
    is_anomaly: bool = Field(..., description="Whether traffic is anomalous")
    anomaly_score: float = Field(..., description="Anomaly score (0-1)")
    confidence: float = Field(..., description="Model confidence")
    explanation: str = Field(..., description="Human-readable explanation")


# ============= Security Models =============

class SecurityAlertType(str, Enum):
    """Types of security alerts"""
    SUSPICIOUS_LOGIN = "suspicious_login"
    FAILED_LOGIN = "failed_login"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    BRUTE_FORCE = "brute_force"
    DEVICE_TAMPERING = "device_tampering"


class SecuritySeverity(str, Enum):
    """Security event severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class SecurityAlert(BaseModel):
    """Security alert model"""
    alert_type: SecurityAlertType = Field(..., description="Type of security alert")
    severity: SecuritySeverity = Field(..., description="Severity level")
    user_email: str = Field(..., description="User email")
    ip_address: str = Field(..., description="IP address of the user")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
