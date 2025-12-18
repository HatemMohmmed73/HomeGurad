import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  FiWifi, 
  FiShield, 
  FiAlertCircle, 
  FiActivity,
  FiLock,
  FiUnlock
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import api from '../services/api';
import { Device, DeviceStatus } from '../types';

interface DeviceCardProps {
  device: Device;
  onUpdate?: (device: Device) => void;
  isUnknown?: boolean;
}

const DeviceCard = ({ device, onUpdate, isUnknown = false }: DeviceCardProps) => {
  const [loading, setLoading] = useState(false);

  const getStatusColor = (status: DeviceStatus) => {
    switch (status) {
      case DeviceStatus.ACTIVE:
        return 'bg-green-100 text-green-700';
      case DeviceStatus.IDLE:
        return 'bg-gray-100 text-gray-700';
      case DeviceStatus.BLOCKED:
        return 'bg-red-100 text-red-700';
      case DeviceStatus.OFFLINE:
        return 'bg-gray-100 text-gray-500';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusIcon = () => {
    if (device.is_blocked) {
      return <FiLock className="text-red-500" />;
    }
    return <FiShield className="text-green-500" />;
  };

  const handleToggleBlock = async (e: React.MouseEvent) => {
    e.preventDefault(); // Prevent navigation
    if (!onUpdate) return;
    
    setLoading(true);
    try {
      const endpoint = device.is_blocked ? 'unblock' : 'block';
      await api.post(`/devices/${device._id}/${endpoint}`);
      
      const updatedDevice = { ...device, is_blocked: !device.is_blocked };
      onUpdate(updatedDevice);
      
      toast.success(
        device.is_blocked ? 'Device unblocked successfully' : 'Device blocked successfully'
      );
    } catch (error) {
      toast.error('Failed to update device');
    } finally {
      setLoading(false);
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow overflow-hidden ${isUnknown ? 'border-2 border-yellow-400' : ''}`}>
      {/* Header */}
      <div className="p-3 sm:p-4 border-b flex items-start justify-between gap-2">
        <div className="flex items-start space-x-2 sm:space-x-3 min-w-0 flex-1">
          <div className="text-lg sm:text-2xl flex-shrink-0 mt-1">{getStatusIcon()}</div>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-gray-800 text-sm sm:text-base truncate">
              {device.hostname || 'Unknown Device'}
            </h3>
            <p className="text-xs sm:text-sm text-gray-500 truncate">{device.ip}</p>
          </div>
        </div>
        <span className={`px-2 py-1 text-xs font-medium rounded whitespace-nowrap flex-shrink-0 ${getStatusColor(device.status)}`}>
          {device.status}
        </span>
      </div>

      {/* Body */}
      <div className="p-3 sm:p-4 space-y-3">
        {/* Stats */}
        <div className="grid grid-cols-2 gap-3 text-xs sm:text-sm">
          <div>
            <p className="text-gray-500">Sent</p>
            <p className="font-medium text-gray-800 text-sm sm:text-base mt-1">
              {formatBytes(device.total_bytes_sent)}
            </p>
          </div>
          <div>
            <p className="text-gray-500">Received</p>
            <p className="font-medium text-gray-800 text-sm sm:text-base mt-1">
              {formatBytes(device.total_bytes_received)}
            </p>
          </div>
        </div>

        {/* MAC Address */}
        <div className="pt-2 border-t">
          <p className="text-xs text-gray-500">MAC Address</p>
          <p className="text-xs font-mono text-gray-700 break-all">{device.mac}</p>
        </div>
        
        {isUnknown && (
          <div className="pt-2 border-t bg-yellow-50 -mx-4 -mb-4 p-4 mt-2">
            <p className="text-xs text-yellow-800 font-medium flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
              New Device Detected
            </p>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 sm:p-4 bg-gray-50 border-t flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-4">
        <Link
          to={`/device/${device._id}`}
          className="text-xs sm:text-sm text-blue-600 hover:text-blue-700 font-medium text-center sm:text-left"
        >
          View Details →
        </Link>
        <button
          onClick={handleToggleBlock}
          disabled={loading}
          className={`w-full sm:w-auto px-3 py-1.5 text-xs sm:text-sm rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center justify-center gap-2 ${
            device.is_blocked
              ? 'bg-green-100 text-green-700 hover:bg-green-200'
              : 'bg-red-100 text-red-700 hover:bg-red-200'
          }`}
        >
          {loading ? (
             <span>...</span> 
          ) : device.is_blocked ? (
             <>
               <FiUnlock className="text-sm" /> Unblock
             </>
          ) : (
             <>
               <FiLock className="text-sm" /> Block
             </>
          )}
        </button>
      </div>
    </div>
  );
};

export default DeviceCard;
