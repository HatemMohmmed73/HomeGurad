import { useCallback, useEffect, useMemo, useState } from 'react';
import { FiAlertTriangle, FiEye, FiShield, FiUnlock, FiX } from 'react-icons/fi';
import { toast } from 'react-toastify';
import api from '../services/api';
import { Alert } from '../types';

interface AlertPopupProps {
  alert: Alert | any | null; // tolerate websocket payload shape
  onClose: () => void;
  onViewDetails?: () => void;
  isModal?: boolean;
}

const AlertPopup = ({ alert, onClose, onViewDetails, isModal = false }: AlertPopupProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isUnblocking, setIsUnblocking] = useState(false);

  const severity = (alert?.severity || 'low') as string;

  const playAlertSound = useCallback(() => {
    try {
      const AudioCtx = (window.AudioContext || (window as any).webkitAudioContext) as typeof AudioContext | undefined;
      if (!AudioCtx) return;

      const ctx = new AudioCtx();
      const oscillator = ctx.createOscillator();
      const gain = ctx.createGain();

      oscillator.type = 'sine';
      oscillator.frequency.value = 880;
      gain.gain.value = 0.0001;

      oscillator.connect(gain);
      gain.connect(ctx.destination);

      const now = ctx.currentTime;
      gain.gain.setValueAtTime(0.0001, now);
      gain.gain.exponentialRampToValueAtTime(0.15, now + 0.02);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.2);

      oscillator.start(now);
      oscillator.stop(now + 0.22);

      oscillator.onended = () => {
        try {
          ctx.close();
        } catch {
          // ignore
        }
      };
    } catch {
      // Autoplay policies may block this; don't crash the UI.
    }
  }, []);

  const getSeverityColor = useCallback(() => {
    switch (String(severity).toLowerCase()) {
      case 'critical':
        return 'border-red-500 bg-red-50 text-red-800';
      case 'high':
        return 'border-orange-500 bg-orange-50 text-orange-800';
      case 'medium':
        return 'border-yellow-500 bg-yellow-50 text-yellow-800';
      case 'low':
      default:
        return 'border-blue-500 bg-blue-50 text-blue-800';
    }
  }, [severity]);

  const severityBadgeClass = useMemo(() => {
    switch (String(severity).toLowerCase()) {
      case 'critical':
        return 'bg-red-600';
      case 'high':
        return 'bg-orange-500';
      case 'medium':
        return 'bg-yellow-500';
      default:
        return 'bg-blue-600';
    }
  }, [severity]);

  const getSeverityIcon = useCallback(() => {
    if (String(severity).toLowerCase() === 'critical') return <FiAlertTriangle className="text-red-600" />;
    if (String(severity).toLowerCase() === 'high') return <FiAlertTriangle className="text-orange-600" />;
    return <FiShield className="text-blue-600" />;
  }, [severity]);

  const deviceIdentifier =
    alert?.device_id || alert?.device_ip || alert?.device_mac || alert?.device?.ip || alert?.device?.mac || null;

  const deviceName = alert?.device_name || alert?.details?.device_name || alert?.device?.name || alert?.device_ip || 'Unknown Device';
  const deviceIp = alert?.device_ip || alert?.device?.ip || 'unknown';
  const alertId = alert?.alert_id || alert?._id || 'unknown';
  const reason = alert?.reason || 'Suspicious activity detected';

  const timestampValue = alert?.timestamp;
  const formattedTimestamp = useMemo(() => {
    try {
      return new Date(timestampValue).toLocaleString();
    } catch {
      return String(timestampValue ?? '');
    }
  }, [timestampValue]);

  const handleAcknowledge = useCallback(async () => {
    if (!alertId || alertId === 'unknown' || alert?.acknowledged) return;
    try {
      await api.patch(`/alerts/${encodeURIComponent(String(alertId))}/acknowledge`);
    } catch {
      // ignore
    }
  }, [alertId, alert?.acknowledged]);

  const handleUnblock = useCallback(async () => {
    if (!deviceIdentifier) {
      toast.error('Cannot unblock: device identifier is missing');
      return;
    }

    try {
      setIsUnblocking(true);
      await api.post(`/devices/${encodeURIComponent(String(deviceIdentifier))}/unblock`);
      toast.success('Device unblocked successfully');
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to unblock device';
      toast.error(msg);
    } finally {
      setIsUnblocking(false);
    }
  }, [deviceIdentifier, handleAcknowledge]);

  const handleClose = useCallback(() => {
    handleAcknowledge();
    setIsVisible(false);
    setTimeout(onClose, 300);
  }, [handleAcknowledge, onClose]);

  useEffect(() => {
    if (!alert) return;
    setIsVisible(true);
    
    // Auto-acknowledge if it's a modal (user is actively viewing it)
    if (isModal) {
        handleAcknowledge();
    }

    if (!isModal) {
      playAlertSound();
      const timer = setTimeout(() => {
        handleClose();
      }, 15000);
      return () => clearTimeout(timer);
    }
  }, [alert, isModal, onClose, playAlertSound, handleAcknowledge, handleClose]);

  if (!alert || !isVisible) return null;

  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in">
        <div className="w-full max-w-md animate-scale-in">
          <div className={`border-l-4 rounded-lg p-6 bg-white border shadow-2xl ${getSeverityColor()}`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex items-start gap-4 flex-1">
                <div className="flex-shrink-0 text-2xl">{getSeverityIcon()}</div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                    Security Alert Details
                    <span className={`px-2 py-0.5 text-xs font-bold rounded uppercase text-white ${severityBadgeClass}`}>
                      {String(severity)}
                    </span>
                  </h3>

                  <p className="font-medium text-gray-800 mb-4 text-lg break-words">{reason}</p>

                  <div className="bg-white/50 rounded p-3 space-y-2 mb-4 text-sm border border-black/5 text-gray-800">
                    <p><strong>Device:</strong> {deviceName}</p>
                    <p><strong>IP Address:</strong> {deviceIp}</p>
                    <p><strong>Alert ID:</strong> {String(alertId)}</p>
                    <p><strong>Time:</strong> {formattedTimestamp}</p>
                    {alert?.action_taken && (
                      <p className="text-blue-700">
                        <strong>Action Taken:</strong>{' '}
                        {typeof alert.action_taken === 'string' ? alert.action_taken : JSON.stringify(alert.action_taken)}
                      </p>
                    )}
                  </div>

                  <div className="flex gap-3 justify-end mt-4">
                    <button
                      onClick={handleUnblock}
                      disabled={isUnblocking}
                      className="flex items-center gap-2 bg-red-600 text-white hover:bg-red-700 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm disabled:opacity-50"
                    >
                      <FiUnlock />
                      {isUnblocking ? 'Unblocking...' : 'Unblock Device'}
                    </button>

                    <button
                      onClick={handleClose}
                      className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm"
                    >
                      Close
                    </button>
                  </div>
                </div>
              </div>

              <button
                onClick={handleClose}
                className="flex-shrink-0 p-1 hover:bg-black/10 rounded transition-colors text-gray-700"
                aria-label="Close"
              >
                <FiX className="text-lg" />
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  // Toast mode
  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right max-w-md w-full sm:w-96 shadow-2xl">
      <div className={`border-l-4 rounded-lg p-4 bg-white border ${getSeverityColor()}`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex-shrink-0 mt-0.5 text-xl">{getSeverityIcon()}</div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-bold text-base text-gray-900">Security Alert!</h3>
                <span className={`px-2 py-0.5 text-xs font-bold rounded uppercase text-white ${severityBadgeClass}`}>
                  {String(severity)}
                </span>
              </div>

              <p className="text-sm font-medium mb-2 break-words text-gray-800">{reason}</p>

              <div className="text-xs space-y-1 mb-3 opacity-90 text-gray-700">
                <p><strong>Device:</strong> {deviceName}</p>
                <p><strong>IP:</strong> {deviceIp}</p>
                <p><strong>Time:</strong> {formattedTimestamp}</p>
              </div>

              <div className="flex flex-wrap gap-2 mt-2">
                <button
                  onClick={handleUnblock}
                  disabled={isUnblocking}
                  className="flex items-center gap-1 bg-white border border-red-200 text-red-700 hover:bg-red-50 px-3 py-1.5 rounded text-xs font-semibold transition-colors shadow-sm disabled:opacity-50"
                >
                  <FiUnlock />
                  {isUnblocking ? 'Unblocking...' : 'Unblock Device'}
                </button>

                {onViewDetails && (
                  <button
                    onClick={() => {
                        handleAcknowledge();
                        onViewDetails();
                    }}
                    className="flex items-center gap-1 bg-white border border-blue-200 text-blue-700 hover:bg-blue-50 px-3 py-1.5 rounded text-xs font-semibold transition-colors shadow-sm"
                  >
                    <FiEye />
                    View details
                  </button>
                )}

                <button
                  onClick={handleClose}
                  className="bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 px-3 py-1.5 rounded text-xs font-semibold transition-colors shadow-sm"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>

          <button
            onClick={handleClose}
            className="flex-shrink-0 p-1 hover:bg-black/10 rounded transition-colors"
            aria-label="Close"
          >
            <FiX className="text-lg" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default AlertPopup;
