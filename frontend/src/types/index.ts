export enum DeviceStatus {
  ACTIVE = 'active',
  IDLE = 'idle',
  BLOCKED = 'blocked',
  OFFLINE = 'offline',
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum AlertType {
  PORT_SCAN = 'port_scan',
  FLOOD = 'flood',
  DATA_EXFILTRATION = 'data_exfiltration',
  UNUSUAL_TRAFFIC = 'unusual_traffic',
  UNKNOWN_DESTINATION = 'unknown_destination',
  ANOMALY = 'anomaly',
}

export interface Device {
  _id: string;
  mac: string;
  ip: string;
  hostname?: string;
  device_type?: string;
  status: DeviceStatus;
  first_seen: string;
  last_seen: string;
  total_bytes_sent: number;
  total_bytes_received: number;
  packet_count: number;
  behavioral_score: number;
  is_blocked: boolean;
  metadata?: Record<string, any>;
}

export interface Alert {
  _id: string;
  device_id: string;
  device_ip: string;
  device_mac: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  anomaly_score: number;
  timestamp: string;
  reason: string;
  details?: Record<string, any>;
  action_taken?: string;
  acknowledged: boolean;
}

export interface SystemSettings {
  auto_block_enabled: boolean;
  anomaly_threshold: number;
  alert_notification_enabled: boolean;
  model_retrain_interval_hours: number;
  zeek_monitoring_enabled: boolean;
  updated_at: string;
}

export interface AlertStats {
  total_alerts: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  top_devices: Array<{ _id: string; count: number }>;
  period_days: number;
}

