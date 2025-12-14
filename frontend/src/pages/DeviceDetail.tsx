import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  FiArrowLeft, 
  FiShield, 
  FiActivity, 
  FiClock,
  FiLock,
  FiUnlock,
  FiEdit2,
  FiCheck,
  FiX
} from 'react-icons/fi';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { toast } from 'react-toastify';
import api from '../services/api';
import { Device, Alert } from '../types';

const DeviceDetail = () => {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const [device, setDevice] = useState<Device | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState('');

  useEffect(() => {
    loadDeviceData();
    
    // Poll for updates every 5 seconds (for file-based data)
    const pollInterval = setInterval(() => {
      loadDeviceData();
    }, 5000);

    return () => {
      clearInterval(pollInterval);
    };
  }, [deviceId]);

  const loadDeviceData = async () => {
    try {
      const [deviceRes, alertsRes] = await Promise.all([
        api.get(`/devices/${deviceId}`),
        api.get(`/alerts?device_id=${deviceId}&limit=20`),
      ]);

      setDevice(deviceRes.data);
      setEditedName(deviceRes.data.hostname || '');
      setAlerts(alertsRes.data);
    } catch (error) {
      toast.error('Failed to load device data');
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleBlock = async () => {
    if (!device) return;

    try {
      const endpoint = device.is_blocked ? 'unblock' : 'block';
      await api.post(`/devices/${device._id}/${endpoint}`);
      
      setDevice({ ...device, is_blocked: !device.is_blocked });
      toast.success(
        device.is_blocked ? 'Device unblocked successfully' : 'Device blocked successfully'
      );
    } catch (error) {
      toast.error('Failed to update device');
    }
  };

  const handleUpdateName = async () => {
    if (!device || !editedName.trim()) return;

    try {
      await api.post(`/devices/${device._id}/name?name=${encodeURIComponent(editedName)}`);
      setDevice({ ...device, hostname: editedName });
      setIsEditingName(false);
      toast.success('Device name updated');
    } catch (error) {
      toast.error('Failed to update device name');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!device) {
    return <div>Device not found</div>;
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-0 mb-4 sm:mb-6">
        <div className="flex items-start space-x-2 sm:space-x-4">
          <button
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors flex-shrink-0 mt-1 sm:mt-0"
          >
            <FiArrowLeft className="text-lg sm:text-xl" />
          </button>
          <div className="min-w-0 flex-1">
            {isEditingName ? (
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  className="px-3 py-1 text-lg sm:text-2xl font-bold text-gray-800 border rounded focus:ring-2 focus:ring-blue-500 outline-none w-full sm:w-auto"
                  autoFocus
                />
                <button
                  onClick={handleUpdateName}
                  className="p-2 bg-green-100 text-green-600 rounded hover:bg-green-200"
                >
                  <FiCheck />
                </button>
                <button
                  onClick={() => {
                    setIsEditingName(false);
                    setEditedName(device.hostname || '');
                  }}
                  className="p-2 bg-red-100 text-red-600 rounded hover:bg-red-200"
                >
                  <FiX />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2 group">
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-800 break-words">
                  {device.hostname || 'Unknown Device'}
                </h1>
                <button
                  onClick={() => setIsEditingName(true)}
                  className="p-1.5 text-gray-400 hover:text-blue-600 transition-colors"
                  title="Edit name"
                >
                  <FiEdit2 className="text-lg" />
                </button>
              </div>
            )}
            <p className="text-xs sm:text-sm text-gray-600 mt-1 break-all">{device.ip}</p>
          </div>
        </div>
        <button
          onClick={handleToggleBlock}
          className={`w-full sm:w-auto px-4 py-2 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2 text-sm sm:text-base whitespace-nowrap ${
            device.is_blocked
              ? 'bg-green-100 text-green-700 hover:bg-green-200'
              : 'bg-red-100 text-red-700 hover:bg-red-200'
          }`}
        >
          {device.is_blocked ? <FiUnlock /> : <FiLock />}
          <span className="hidden sm:inline">{device.is_blocked ? 'Unblock Device' : 'Block Device'}</span>
          <span className="sm:hidden">{device.is_blocked ? 'Unblock' : 'Block'}</span>
        </button>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4 lg:gap-6">
        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <FiActivity className="text-xl sm:text-2xl text-blue-600 flex-shrink-0" />
            <h3 className="font-semibold text-gray-800 text-sm sm:text-base">Traffic</h3>
          </div>
          <div className="space-y-2 text-xs sm:text-sm">
            <div>
              <p className="text-gray-500">Sent</p>
              <p className="text-lg sm:text-xl font-bold text-gray-800 mt-1">
                {formatBytes(device.total_bytes_sent)}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Received</p>
              <p className="text-lg sm:text-xl font-bold text-gray-800 mt-1">
                {formatBytes(device.total_bytes_received)}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Packets</p>
              <p className="text-lg sm:text-xl font-bold text-gray-800 mt-1">
                {device.packet_count.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <FiShield className="text-xl sm:text-2xl text-green-600 flex-shrink-0" />
            <h3 className="font-semibold text-gray-800 text-sm sm:text-base">Security</h3>
          </div>
          <div className="space-y-3 text-xs sm:text-sm">
            <div>
              <p className="text-gray-500">Status</p>
              <p className="text-sm sm:text-base font-semibold text-gray-800 capitalize mt-1">
                {device.status}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Block Status</p>
              <p className={`text-sm sm:text-base font-semibold mt-1 ${device.is_blocked ? 'text-red-600' : 'text-green-600'}`}>
                {device.is_blocked ? 'Blocked' : 'Allowed'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6">
          <div className="flex items-center space-x-3 mb-4">
            <FiClock className="text-xl sm:text-2xl text-purple-600 flex-shrink-0" />
            <h3 className="font-semibold text-gray-800 text-sm sm:text-base">Activity</h3>
          </div>
          <div className="space-y-2 text-xs sm:text-sm">
            <div>
              <p className="text-gray-500">First Seen</p>
              <p className="text-xs sm:text-sm font-medium text-gray-800 mt-1 break-words">
                {new Date(device.first_seen).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Last Seen</p>
              <p className="text-xs sm:text-sm font-medium text-gray-800 mt-1 break-words">
                {new Date(device.last_seen).toLocaleString()}
              </p>
            </div>
            <div>
              <p className="text-gray-500">MAC Address</p>
              <p className="text-xs sm:text-sm font-mono font-medium text-gray-800 mt-1 break-all">
                {device.mac}
              </p>
            </div>
            <div>
              <p className="text-gray-500">Device Type</p>
              <p className="text-xs sm:text-sm font-medium text-gray-800 capitalize mt-1">
                {device.device_type || 'Unknown'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts History */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 sm:p-6 border-b">
          <h2 className="text-lg sm:text-xl font-bold text-gray-800">Alert History</h2>
        </div>
        <div className="divide-y max-h-96 overflow-y-auto">
          {alerts.length === 0 ? (
            <div className="p-6 sm:p-8 text-center text-sm sm:text-base text-gray-500">
              No alerts for this device
            </div>
          ) : (
            alerts.map((alert) => (
              <div key={alert._id} className="p-3 sm:p-4 hover:bg-gray-50 transition-colors">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 text-sm sm:text-base break-words">{alert.reason}</p>
                    <p className="text-xs sm:text-sm text-gray-500 mt-1">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs font-medium rounded whitespace-nowrap flex-shrink-0 ${
                      alert.severity === 'critical'
                        ? 'bg-red-100 text-red-700'
                        : alert.severity === 'high'
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-yellow-100 text-yellow-700'
                    }`}
                  >
                    {alert.severity}
                  </span>
                </div>
                <div className="mt-2 text-xs sm:text-sm text-gray-600 break-words">
                  Type: {alert.alert_type}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default DeviceDetail;
