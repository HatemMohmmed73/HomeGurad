import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { 
  FiWifi, 
  FiShield, 
  FiAlertTriangle, 
  FiActivity,
  FiCheckCircle,
  FiXCircle
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import api from '../services/api';
import websocket from '../services/websocket';
import notifications from '../services/notifications';
import pushSubscription from '../services/pushSubscription';
import { Device, Alert, DeviceStatus } from '../types';
import DeviceCard from '../components/DeviceCard';
import StatsCard from '../components/StatsCard';
import AlertPopup from '../components/AlertPopup';

const Dashboard = () => {
  const navigate = useNavigate();
  const [devices, setDevices] = useState<Device[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [newAlert, setNewAlert] = useState<Alert | null>(null);

  useEffect(() => {
    loadData();
    
    // Initialize and subscribe to push notifications
    const initPushNotifications = async () => {
      const initialized = await pushSubscription.initialize();
      if (initialized) {
        const isSubscribed = await pushSubscription.isSubscribed();
        if (!isSubscribed) {
          const subscribed = await pushSubscription.subscribe();
          if (subscribed) {
            toast.success('Push notifications enabled! You will receive alerts even when the browser is closed.');
          } else {
            toast.info('Enable push notifications to receive alerts when you\'re away');
          }
        }
      }
    };
    
    initPushNotifications();
    
    // Also enable browser notifications for when tab is inactive
    if (notifications.isSupported()) {
      notifications.requestPermission();
    }
    
    // Connect to WebSocket for real-time updates
    websocket.connectDevices((data) => {
      updateDevice(data.data);
    });

    websocket.connectAlerts((message) => {
      // Handle WebSocket alert message
      if (message.type === 'new_alert' && message.data) {
        const alertData = message.data;
        
        // Create Alert object from WebSocket data
        const newAlertObj: Alert = {
          _id: alertData.alert_id || alertData.device_ip,
          device_id: alertData.device_ip,
          device_ip: alertData.device_ip,
          device_mac: alertData.device_mac || alertData.device_ip,
          device_name: alertData.device_name || alertData.device_ip,
          alert_type: 'anomaly',
          severity: alertData.severity || 'medium',
          anomaly_score: alertData.anomaly_score || 0.0,
          timestamp: alertData.timestamp ? new Date(alertData.timestamp * 1000).toISOString() : new Date().toISOString(),
          reason: alertData.reason || 'Anomalous activity detected',
          details: {},
          action_taken: alertData.action_taken || null,
          acknowledged: alertData.status === 'acknowledged'
        };
        
        // Show popup notification (when dashboard is open)
        setNewAlert(newAlertObj);
        
        // Show browser notification (works even when tab is not active)
        notifications.showAlertNotification({
          reason: newAlertObj.reason,
          device_name: newAlertObj.device_name,
          severity: newAlertObj.severity,
          alert_id: newAlertObj._id,
        });
        
        // Show toast notification
        toast.warning(`New Alert: ${newAlertObj.reason}`, {
          position: 'top-right',
          autoClose: 5000,
        });
        
        // Update recent alerts list
        setRecentAlerts((prev) => [newAlertObj, ...prev.slice(0, 4)]);
      }
    });

    // Poll for updates every 5 seconds (for file-based data)
    const pollInterval = setInterval(() => {
      loadData();
    }, 5000);

    return () => {
      websocket.disconnectAll();
      clearInterval(pollInterval);
    };
  }, []);

  const loadData = async () => {
    try {
      const [devicesRes, alertsRes] = await Promise.all([
        api.get('/devices'),
        api.get('/alerts?limit=5'),
      ]);

      setDevices(devicesRes.data);
      setRecentAlerts(alertsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const updateDevice = (updatedDevice: Device) => {
    setDevices((prev) =>
      prev.map((d) => (d._id === updatedDevice._id ? updatedDevice : d))
    );
  };

  const stats = {
    total: devices.length,
    active: devices.filter((d) => d.status === DeviceStatus.ACTIVE).length,
    blocked: devices.filter((d) => d.is_blocked).length,
    alerts: recentAlerts.filter((a) => !a.acknowledged).length,
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <>
      {/* Alert Popup Notification */}
      <AlertPopup
        alert={newAlert}
        onClose={() => setNewAlert(null)}
        onViewDetails={() => navigate('/alerts')}
      />
      
      <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-800 mb-1 sm:mb-2">Dashboard</h1>
        <p className="text-sm sm:text-base text-gray-600">Monitor your IoT devices in real-time</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
        <StatsCard
          title="Total"
          value={stats.total}
          icon={FiWifi}
          color="blue"
        />
        <StatsCard
          title="Active"
          value={stats.active}
          icon={FiCheckCircle}
          color="green"
        />
        <StatsCard
          title="Blocked"
          value={stats.blocked}
          icon={FiXCircle}
          color="red"
        />
        <StatsCard
          title="Alerts"
          value={stats.alerts}
          icon={FiAlertTriangle}
          color="yellow"
        />
      </div>

      {/* Devices Grid */}
      <div>
        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-800 mb-3 sm:mb-4">Devices</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
          {devices.map((device) => (
            <Link
              key={device._id}
              to={`/device/${device._id}`}
              className="transform hover:scale-105 transition-transform"
            >
              <DeviceCard device={device} />
            </Link>
          ))}
        </div>
      </div>

      {/* Recent Alerts */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 sm:gap-0 mb-3 sm:mb-4">
          <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-800">Recent Alerts</h2>
          <Link
            to="/alerts"
            className="text-blue-600 hover:text-blue-700 font-medium text-sm sm:text-base"
          >
            View all →
          </Link>
        </div>
        <div className="space-y-2 sm:space-y-3">
          {recentAlerts.map((alert) => (
            <div
              key={alert._id}
              className={`p-3 sm:p-4 rounded-lg border-l-4 ${
                alert.severity === 'high'
                  ? 'border-red-500 bg-red-50'
                  : alert.severity === 'medium'
                  ? 'border-yellow-500 bg-yellow-50'
                  : 'border-blue-500 bg-blue-50'
              }`}
            >
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-gray-800 text-sm sm:text-base break-words">{alert.reason}</p>
                  <p className="text-xs sm:text-sm text-gray-600 mt-1">{alert.device_name}</p>
                </div>
                <span className={`px-2 sm:px-3 py-1 rounded text-xs font-semibold capitalize whitespace-nowrap ${
                  alert.severity === 'high'
                    ? 'text-red-700 bg-red-100'
                    : alert.severity === 'medium'
                    ? 'text-yellow-700 bg-yellow-100'
                    : 'text-blue-700 bg-blue-100'
                }`}>
                  {alert.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
    </>
  );
};

export default Dashboard;
