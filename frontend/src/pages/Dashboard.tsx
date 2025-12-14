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
import { Device, Alert, DeviceStatus } from '../types';
import DeviceCard from '../components/DeviceCard';
import StatsCard from '../components/StatsCard';
import AlertPopup from '../components/AlertPopup';

const Dashboard = () => {
  const navigate = useNavigate();
  const [devices, setDevices] = useState<Device[]>([]);
  const [recentAlerts, setRecentAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [loading, setLoading] = useState(true);

  const updateDevice = (updatedDevice: Device) => {
    setDevices((prevDevices) => {
      const exists = prevDevices.find((d) => d._id === updatedDevice._id);
      if (exists) {
        return prevDevices.map((d) => 
          d._id === updatedDevice._id ? updatedDevice : d
        );
      }
      return [...prevDevices, updatedDevice];
    });
  };

  useEffect(() => {
    loadData();
    
    // Connect to WebSocket for real-time updates (Devices Only)
    websocket.connectDevices((data) => {
      updateDevice(data.data);
    });

    // Poll for updates every 5 seconds (for file-based data)
    const pollInterval = setInterval(() => {
      loadData();
    }, 5000);

    return () => {
      websocket.disconnectDevices();
      clearInterval(pollInterval);
    };
  }, []);

  const loadData = async () => {
    try {
      const [devicesRes, alertsRes] = await Promise.all([
        api.get('/devices'),
        api.get('/alerts?limit=5&days=30'),
      ]);

      setDevices(devicesRes.data);
      // Map alerts to include device_name from details
      const mappedAlerts = alertsRes.data.map((alert: Alert) => ({
        ...alert,
        device_name: alert.details?.device_name || alert.device_ip || 'Unknown Device',
      }));
      setRecentAlerts(mappedAlerts);
    } catch (error) {
      // toast.error('Failed to load data'); // Suppress error toast on poll
    } finally {
      setLoading(false);
    }
  };

  const handleToggleBlock = async (e: React.MouseEvent, device: Device) => {
    e.preventDefault();
    e.stopPropagation();
    
    try {
      const action = device.is_blocked ? 'unblock' : 'block';
      await api.post(`/devices/${device._id}/${action}`);
      toast.success(`Device ${action}ed successfully`);
      
      // Update local state
      setDevices(devices.map(d => 
        d._id === device._id 
          ? { ...d, is_blocked: !d.is_blocked, status: !d.is_blocked ? 'blocked' : 'active' as DeviceStatus } 
          : d
      ));
    } catch (error) {
      toast.error(`Failed to ${device.is_blocked ? 'unblock' : 'block'} device`);
    }
  };

  // Filter devices
  const knownDevices = devices.filter(d => 
    d.hostname && 
    !d.hostname.includes('Unknown') && 
    !d.hostname.includes('External')
  );
  
  const unknownDevices = devices.filter(d => 
    !d.hostname || 
    d.hostname.includes('Unknown') || 
    d.hostname.includes('External')
  );

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <AlertPopup 
        alert={selectedAlert} 
        onClose={() => setSelectedAlert(null)} 
        isModal={true}
      />
      
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">Dashboard Overview</h1>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <span className="w-2 h-2 rounded-full bg-green-500"></span>
          System Active
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatsCard
          title="Total Devices"
          value={devices.length}
          icon={FiWifi}
          color="blue"
        />
        <StatsCard
          title="Active Alerts"
          value={recentAlerts.length}
          icon={FiAlertTriangle}
          color="red"
        />
        <StatsCard
          title="Blocked Devices"
          value={devices.filter(d => d.is_blocked).length}
          icon={FiShield}
          color="orange"
        />
        <StatsCard
          title="Network Status"
          value="Secure"
          icon={FiCheckCircle}
          color="green"
        />
      </div>

      {/* Known Devices Section */}
      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <FiCheckCircle className="text-green-600" />
          Known Devices
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {knownDevices.length === 0 ? (
            <div className="col-span-full p-8 text-center bg-white rounded-lg border border-dashed border-gray-300">
              <p className="text-gray-500">No known devices found</p>
            </div>
          ) : (
            knownDevices.map((device) => (
              <DeviceCard 
                key={device._id} 
                device={device} 
                onUpdate={() => handleToggleBlock}
              />
            ))
          )}
        </div>
      </div>

      {/* Unknown/New Devices Section */}
      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-4 flex items-center gap-2">
          <FiAlertTriangle className="text-orange-500" />
          Unknown / New Devices
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {unknownDevices.length === 0 ? (
            <div className="col-span-full p-8 text-center bg-white rounded-lg border border-dashed border-gray-300">
              <p className="text-gray-500">No unknown devices detected</p>
            </div>
          ) : (
            unknownDevices.map((device) => (
              <DeviceCard 
                key={device._id} 
                device={device} 
                isUnknown={true}
                onUpdate={() => handleToggleBlock}
              />
            ))
          )}
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-6 border-b border-gray-100 flex justify-between items-center">
          <h2 className="text-lg font-bold text-gray-800">Recent Alerts</h2>
          <Link to="/alerts" className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            View all →
          </Link>
        </div>
        <div className="divide-y divide-gray-100">
          {recentAlerts.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              No recent alerts
            </div>
          ) : (
            recentAlerts.map((alert) => (
              <div 
                key={alert._id} 
                onClick={() => setSelectedAlert(alert)}
                className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="flex items-start gap-4">
                  <div className={`p-2 rounded-lg ${
                    alert.severity === 'critical' ? 'bg-red-100 text-red-600' :
                    alert.severity === 'high' ? 'bg-orange-100 text-orange-600' :
                    'bg-yellow-100 text-yellow-600'
                  }`}>
                    <FiActivity />
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="font-medium text-gray-900">{alert.reason}</h3>
                        <p className="text-sm text-gray-500">
                          Device: {alert.device_name}
                        </p>
                      </div>
                      <span className="text-xs text-gray-400">
                        {new Date(alert.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
