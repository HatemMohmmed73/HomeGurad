import { useEffect, useState, useCallback } from 'react';
import { FiAlertTriangle, FiX, FiShield, FiUnlock } from 'react-icons/fi';
import { Alert } from '../types';
import api from '../services/api';
import { toast } from 'react-toastify';

interface AlertPopupProps {
  alert: Alert | null;
  onClose: () => void;
  onViewDetails?: () => void;
  isModal?: boolean; // New prop for modal mode
}

const AlertPopup = ({ alert, onClose, onViewDetails, isModal = false }: AlertPopupProps) => {
  const [isVisible, setIsVisible] = useState(false);
  const [isUnblocking, setIsUnblocking] = useState(false);

  // ... (playAlertSound logic remains same)

  useEffect(() => {
    if (alert) {
      setIsVisible(true);
      if (!isModal) {
        playAlertSound();
        // Auto-close only if NOT in modal mode
        const timer = setTimeout(() => {
          setIsVisible(false);
          setTimeout(onClose, 300);
        }, 15000);
        return () => clearTimeout(timer);
      }
    }
  }, [alert, onClose, playAlertSound, isModal]);

  // ... (handleUnblock remains same)

  if (!alert || !isVisible) return null;

  // ... (helper functions remain same)

  // Conditional Rendering for Modal vs Toast
  if (isModal) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 animate-fade-in">
        <div className="w-full max-w-md animate-scale-in">
           {/* Reusing the same card structure but removing fixed positioning */}
           <div className={`${getSeverityColor()} border-l-4 rounded-lg p-6 bg-white border shadow-2xl`}>
             {/* Content similar to below but adapted for modal */}
             <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-4 flex-1">
                  <div className="flex-shrink-0 text-2xl">
                    {getSeverityIcon()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-bold text-lg mb-2 flex items-center gap-2">
                      Security Alert Details
                      <span className={`px-2 py-0.5 text-xs font-bold rounded uppercase text-white ${
                        alert.severity?.toLowerCase() === 'critical' ? 'bg-red-600' : 
                        alert.severity?.toLowerCase() === 'high' ? 'bg-orange-500' : 'bg-yellow-500'
                      }`}>
                        {alert.severity}
                      </span>
                    </h3>
                    
                    <p className="font-medium text-gray-800 mb-4 text-lg">
                      {alert.reason}
                    </p>
                    
                    <div className="bg-white/50 rounded p-3 space-y-2 mb-4 text-sm border border-black/5">
                      <p><strong>Device:</strong> {alert.device_name || alert.device_ip}</p>
                      <p><strong>IP Address:</strong> {alert.device_ip}</p>
                      <p><strong>Alert ID:</strong> {alert.alert_id || alert._id}</p>
                      <p><strong>Time:</strong> {new Date(alert.timestamp).toLocaleString()}</p>
                      {alert.action_taken && (
                         <p className="text-blue-700"><strong>Action Taken:</strong> {alert.action_taken}</p>
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
                        onClick={() => {
                          setIsVisible(false);
                          setTimeout(onClose, 300);
                        }}
                        className="bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 px-4 py-2 rounded-lg text-sm font-semibold transition-colors shadow-sm"
                      >
                        Close
                      </button>
                    </div>
                  </div>
                </div>
             </div>
           </div>
        </div>
      </div>
    );
  }

  // Toast Mode (Original)
  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right max-w-md w-full sm:w-96 shadow-2xl">
      {/* Original Content */}
      <div className={`${getSeverityColor()} border-l-4 rounded-lg p-4 bg-white border`}>
        {/* ... same as original ... */}
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex-shrink-0 mt-0.5 text-xl">
              {getSeverityIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-bold text-base">
                  Security Alert!
                </h3>
                <span className={`px-2 py-0.5 text-xs font-bold rounded uppercase text-white ${
                  alert.severity?.toLowerCase() === 'critical' ? 'bg-red-600' : 
                  alert.severity?.toLowerCase() === 'high' ? 'bg-orange-500' : 'bg-yellow-500'
                }`}>
                  {alert.severity}
                </span>
              </div>
              
              <p className="text-sm font-medium mb-2 break-words">
                {alert.reason}
              </p>
              
              <div className="text-xs space-y-1 mb-3 opacity-90">
                <p><strong>Device:</strong> {alert.device_name || alert.device_ip}</p>
                <p><strong>IP:</strong> {alert.device_ip}</p>
                <p><strong>Time:</strong> {new Date(alert.timestamp).toLocaleTimeString()}</p>
              </div>

              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleUnblock}
                  disabled={isUnblocking}
                  className="flex items-center gap-1 bg-white border border-red-200 text-red-700 hover:bg-red-50 px-3 py-1.5 rounded text-xs font-semibold transition-colors shadow-sm"
                >
                  <FiUnlock />
                  {isUnblocking ? 'Unblocking...' : 'Unblock Device'}
                </button>
                
                <button
                  onClick={() => {
                    setIsVisible(false);
                    setTimeout(onClose, 300);
                  }}
                  className="bg-white border border-gray-200 text-gray-600 hover:bg-gray-50 px-3 py-1.5 rounded text-xs font-semibold transition-colors shadow-sm"
                >
                  Dismiss
                </button>
              </div>
            </div>
          </div>
          <button
            onClick={() => {
              setIsVisible(false);
              setTimeout(onClose, 300);
            }}
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
