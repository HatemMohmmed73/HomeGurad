import { useEffect, useState } from 'react';
import { FiAlertTriangle, FiX, FiShield } from 'react-icons/fi';
import { Alert } from '../types';

interface AlertPopupProps {
  alert: Alert | null;
  onClose: () => void;
  onViewDetails?: () => void;
}

const AlertPopup = ({ alert, onClose, onViewDetails }: AlertPopupProps) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (alert) {
      setIsVisible(true);
      // Auto-close after 10 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        setTimeout(onClose, 300); // Wait for animation
      }, 10000);
      return () => clearTimeout(timer);
    }
  }, [alert, onClose]);

  if (!alert || !isVisible) return null;

  const getSeverityColor = () => {
    switch (alert.severity?.toLowerCase()) {
      case 'critical':
      case 'high':
        return 'bg-red-50 border-red-500 text-red-800';
      case 'medium':
        return 'bg-orange-50 border-orange-500 text-orange-800';
      default:
        return 'bg-yellow-50 border-yellow-500 text-yellow-800';
    }
  };

  const getSeverityIcon = () => {
    switch (alert.severity?.toLowerCase()) {
      case 'critical':
      case 'high':
        return <FiShield className="text-red-600" />;
      default:
        return <FiAlertTriangle className="text-orange-600" />;
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 animate-slide-in-right max-w-md w-full sm:w-96">
      <div className={`${getSeverityColor()} border-l-4 rounded-lg shadow-xl p-4`}>
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3 flex-1">
            <div className="flex-shrink-0 mt-0.5">
              {getSeverityIcon()}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <h3 className="font-bold text-sm sm:text-base">
                  New Security Alert
                </h3>
                <span className="px-2 py-0.5 text-xs font-semibold rounded bg-white/50 capitalize">
                  {alert.severity}
                </span>
              </div>
              <p className="text-sm font-medium mb-1 break-words">
                {alert.reason}
              </p>
              <p className="text-xs opacity-75 mb-2">
                Device: {alert.device_name || alert.device_ip}
              </p>
              {onViewDetails && (
                <button
                  onClick={() => {
                    setIsVisible(false);
                    setTimeout(() => {
                      onViewDetails();
                      onClose();
                    }, 300);
                  }}
                  className="text-xs font-semibold underline hover:no-underline"
                >
                  View Details →
                </button>
              )}
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

