import { useEffect, useState } from 'react';
import { 
  FiAlertTriangle, 
  FiFilter, 
  FiCheckCircle 
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import api from '../services/api';
import { Alert, AlertSeverity, AlertStats } from '../types';

const Alerts = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<AlertStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<AlertSeverity | 'all'>('all');
  const [days, setDays] = useState(7);

  useEffect(() => {
    loadData();
    
    // Poll for updates every 5 seconds (for file-based data)
    const pollInterval = setInterval(() => {
      loadData();
    }, 5000);

    return () => {
      clearInterval(pollInterval);
    };
  }, [filter, days]);

  const loadData = async () => {
    try {
      const severityParam = filter !== 'all' ? `&severity=${filter}` : '';
      const [alertsRes, statsRes] = await Promise.all([
        api.get(`/alerts?days=${days}${severityParam}&limit=100`),
        api.get(`/alerts/stats/summary?days=${days}`),
      ]);

      // Map alerts to include device_name from details
      const mappedAlerts = alertsRes.data.map((alert: Alert) => ({
        ...alert,
        device_name: alert.details?.device_name || alert.device_ip || 'Unknown Device',
      }));
      setAlerts(mappedAlerts);
      setStats(statsRes.data);
    } catch (error) {
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const handleAcknowledge = async (alertId: string) => {
    try {
      await api.patch(`/alerts/${alertId}/acknowledge`);
      setAlerts(alerts.map(a => 
        a._id === alertId ? { ...a, acknowledged: true } : a
      ));
      toast.success('Alert acknowledged');
    } catch (error) {
      toast.error('Failed to acknowledge alert');
    }
  };

  const getSeverityColor = (severity: AlertSeverity) => {
    switch (severity) {
      case AlertSeverity.CRITICAL:
        return 'bg-red-100 text-red-700 border-red-300';
      case AlertSeverity.HIGH:
        return 'bg-orange-100 text-orange-700 border-orange-300';
      case AlertSeverity.MEDIUM:
        return 'bg-yellow-100 text-yellow-700 border-yellow-300';
      case AlertSeverity.LOW:
        return 'bg-blue-100 text-blue-700 border-blue-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Header */}
      <div className="mb-4 sm:mb-6">
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-800 mb-1 sm:mb-2">Security Alerts</h1>
        <p className="text-sm sm:text-base text-gray-600">Monitor and manage security events</p>
      </div>

      {/* Stats Summary */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6">
          <div className="bg-white rounded-lg shadow-sm p-3 sm:p-6 border-l-4 border-blue-500">
            <p className="text-xs sm:text-sm text-gray-600 mb-1">Total</p>
            <p className="text-2xl sm:text-3xl font-bold text-gray-800">{stats.total_alerts}</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-3 sm:p-6 border-l-4 border-red-500">
            <p className="text-xs sm:text-sm text-gray-600 mb-1">Critical</p>
            <p className="text-2xl sm:text-3xl font-bold text-red-600">
              {stats.by_severity.critical || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-3 sm:p-6 border-l-4 border-orange-500">
            <p className="text-xs sm:text-sm text-gray-600 mb-1">High</p>
            <p className="text-2xl sm:text-3xl font-bold text-orange-600">
              {stats.by_severity.high || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-3 sm:p-6 border-l-4 border-yellow-500">
            <p className="text-xs sm:text-sm text-gray-600 mb-1">Med & Low</p>
            <p className="text-2xl sm:text-3xl font-bold text-yellow-600">
              {(stats.by_severity.medium || 0) + (stats.by_severity.low || 0)}
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 items-start sm:items-center">
          <div className="flex items-center space-x-2 text-gray-600 flex-shrink-0">
            <FiFilter className="text-lg" />
            <span className="text-sm font-medium hidden sm:inline">Filter:</span>
          </div>
          <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as AlertSeverity | 'all')}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">All Severities</option>
              <option value={AlertSeverity.CRITICAL}>Critical</option>
              <option value={AlertSeverity.HIGH}>High</option>
              <option value={AlertSeverity.MEDIUM}>Medium</option>
              <option value={AlertSeverity.LOW}>Low</option>
            </select>

            <select
              value={days}
              onChange={(e) => setDays(parseInt(e.target.value))}
              className="px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>

          <button
            onClick={loadData}
            className="w-full sm:w-auto px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Refresh
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {alerts.length === 0 ? (
          <div className="p-8 sm:p-12 text-center">
            <FiCheckCircle className="text-4xl sm:text-6xl text-green-300 mx-auto mb-3 sm:mb-4" />
            <p className="text-sm sm:text-base text-gray-500">No alerts found for the selected filters</p>
          </div>
        ) : (
          <div className="divide-y">
            {alerts.map((alert) => (
              <div
                key={alert._id}
                className={`p-3 sm:p-4 hover:bg-gray-50 transition-colors ${
                  alert.acknowledged ? 'opacity-60' : ''
                }`}
              >
                <div className="flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-4">
                  <FiAlertTriangle
                    className={`text-xl sm:text-2xl flex-shrink-0 mt-0.5 ${
                      alert.severity === AlertSeverity.CRITICAL
                        ? 'text-red-600'
                        : alert.severity === AlertSeverity.HIGH
                        ? 'text-orange-500'
                        : 'text-yellow-500'
                    }`}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-2 flex-wrap">
                      <span
                        className={`px-2 py-1 text-xs font-medium rounded border w-fit ${getSeverityColor(
                          alert.severity
                        )}`}
                      >
                        {alert.severity}
                      </span>
                      <span className="text-xs text-gray-500">
                        {alert.alert_type.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <p className="font-medium text-gray-800 mb-2 text-sm sm:text-base break-words">{alert.reason}</p>
                    <div className="flex flex-col sm:flex-row gap-1 sm:gap-4 text-xs sm:text-sm text-gray-500 flex-wrap">
                      <span className="break-all">Device: {alert.device_ip}</span>
                      <span className="hidden sm:inline">•</span>
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                      <span className="hidden sm:inline">•</span>
                      <span>Score: {(alert.anomaly_score * 100).toFixed(1)}%</span>
                    </div>
                    {alert.action_taken && (
                      <p className="text-xs sm:text-sm text-blue-600 mt-2">
                        Action: {alert.action_taken}
                      </p>
                    )}
                  </div>
                  <div className="w-full sm:w-auto">
                    {!alert.acknowledged && (
                      <button
                        onClick={() => handleAcknowledge(alert._id)}
                        className="w-full sm:w-auto px-3 py-1.5 text-xs sm:text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors whitespace-nowrap"
                      >
                        Acknowledge
                      </button>
                    )}
                    {alert.acknowledged && (
                      <span className="px-3 py-1.5 text-xs sm:text-sm text-gray-500">
                        Acknowledged
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Alerts;
