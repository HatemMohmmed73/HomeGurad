import { useEffect, useState } from 'react';
import { 
  FiShield, 
  FiBell, 
  FiActivity,
  FiSave,
  FiRefreshCw,
} from 'react-icons/fi';
import { toast } from 'react-toastify';
import api from '../services/api';
import { SystemSettings } from '../types';

const Settings = () => {
  const [settings, setSettings] = useState<SystemSettings | null>(null);
  const [modelStatus, setModelStatus] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [settingsRes, modelRes] = await Promise.all([
        api.get('/settings'),
        api.get('/model/status'),
      ]);

      setSettings(settingsRes.data);
      setModelStatus(modelRes.data);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setSaving(true);
    try {
      await api.post('/settings', settings);
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      await api.post('/model/retrain');
      toast.success('Model retraining started');
      // Reload model status
      const modelRes = await api.get('/model/status');
      setModelStatus(modelRes.data);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Failed to retrain model');
    } finally {
      setRetraining(false);
    }
  };

  const handleUpdateThreshold = async (threshold: number) => {
    try {
      await api.post('/model/threshold', null, {
        params: { threshold }
      });
      toast.success('Threshold updated');
      loadData();
    } catch (error) {
      toast.error('Failed to update threshold');
    }
  };

  if (loading || !settings) {
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
        <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-800 mb-1 sm:mb-2">Settings</h1>
        <p className="text-sm sm:text-base text-gray-600">Configure your HomeGuard system</p>
      </div>

      {/* Security Settings */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 sm:p-6 border-b">
          <div className="flex items-center space-x-3">
            <FiShield className="text-xl sm:text-2xl text-blue-600 flex-shrink-0" />
            <h2 className="text-lg sm:text-xl font-bold text-gray-800">Security Settings</h2>
          </div>
        </div>
        <div className="p-4 sm:p-6 space-y-6">
          {/* Auto Block */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-800 mb-1 text-sm sm:text-base">Automatic Blocking</h3>
              <p className="text-xs sm:text-sm text-gray-600">Automatically block devices when anomalies are detected</p>
            </div>
            <button
              onClick={() =>
                setSettings({
                  ...settings,
                  auto_block_enabled: !settings.auto_block_enabled,
                })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
                settings.auto_block_enabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.auto_block_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Anomaly Threshold */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-gray-800 text-sm sm:text-base">Anomaly Threshold</h3>
              <span className="text-xs sm:text-sm font-medium text-gray-600">
                {(settings.anomaly_threshold * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={settings.anomaly_threshold}
              onChange={(e) => {
                const newThreshold = parseFloat(e.target.value);
                setSettings({ ...settings, anomaly_threshold: newThreshold });
              }}
              onMouseUp={(e) => {
                const newThreshold = parseFloat((e.target as HTMLInputElement).value);
                handleUpdateThreshold(newThreshold);
              }}
              className="w-full"
            />
            <p className="text-xs sm:text-sm text-gray-600 mt-2">Lower = more sensitive (more alerts). Higher = less sensitive.</p>
          </div>

          {/* Zeek Monitoring */}
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-800 mb-1 text-sm sm:text-base">Zeek Monitoring</h3>
              <p className="text-xs sm:text-sm text-gray-600">Enable Zeek network traffic monitoring</p>
            </div>
            <button
              onClick={() =>
                setSettings({
                  ...settings,
                  zeek_monitoring_enabled: !settings.zeek_monitoring_enabled,
                })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
                settings.zeek_monitoring_enabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.zeek_monitoring_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* Notification Settings */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 sm:p-6 border-b">
          <div className="flex items-center space-x-3">
            <FiBell className="text-xl sm:text-2xl text-yellow-600 flex-shrink-0" />
            <h2 className="text-lg sm:text-xl font-bold text-gray-800">Notifications</h2>
          </div>
        </div>
        <div className="p-4 sm:p-6 space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-3">
            <div className="flex-1">
              <h3 className="font-semibold text-gray-800 mb-1 text-sm sm:text-base">Alert Notifications</h3>
              <p className="text-xs sm:text-sm text-gray-600">Enable real-time alert notifications</p>
            </div>
            <button
              onClick={() =>
                setSettings({
                  ...settings,
                  alert_notification_enabled: !settings.alert_notification_enabled,
                })
              }
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors flex-shrink-0 ${
                settings.alert_notification_enabled ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  settings.alert_notification_enabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* ML Model Settings */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-4 sm:p-6 border-b">
          <div className="flex items-center space-x-3">
            <FiActivity className="text-xl sm:text-2xl text-purple-600 flex-shrink-0" />
            <h2 className="text-lg sm:text-xl font-bold text-gray-800">ML Model</h2>
          </div>
        </div>
        <div className="p-4 sm:p-6 space-y-6">
          {/* Model Status */}
          {modelStatus && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3 text-sm sm:text-base">Model Status</h3>
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 text-xs sm:text-sm">
                <div>
                  <p className="text-gray-600">Type</p>
                  <p className="font-medium text-gray-800 text-sm sm:text-base">{modelStatus.model_type}</p>
                </div>
                <div>
                  <p className="text-gray-600">Loaded</p>
                  <p className="font-medium text-gray-800 text-sm sm:text-base">
                    {modelStatus.model_loaded ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Predictions</p>
                  <p className="font-medium text-gray-800 text-sm sm:text-base">
                    {modelStatus.total_predictions.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">Anomaly Rate</p>
                  <p className="font-medium text-gray-800 text-sm sm:text-base">
                    {(modelStatus.anomaly_rate * 100).toFixed(1)}%
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Retrain Interval */}
          <div>
            <label className="block font-semibold text-gray-800 mb-2 text-sm sm:text-base">Retrain Interval (hours)</label>
            <input
              type="number"
              min="1"
              max="168"
              value={settings.model_retrain_interval_hours}
              onChange={(e) =>
                setSettings({
                  ...settings,
                  model_retrain_interval_hours: parseInt(e.target.value),
                })
              }
              className="w-full px-3 sm:px-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
            <p className="text-xs sm:text-sm text-gray-600 mt-2">How often the model should be retrained with new data</p>
          </div>

          {/* Retrain Button */}
          <button
            onClick={handleRetrain}
            disabled={retraining}
            className="w-full flex items-center justify-center space-x-2 px-4 py-3 text-sm bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            <FiRefreshCw className={`flex-shrink-0 ${retraining ? 'animate-spin' : ''}`} />
            <span>{retraining ? 'Retraining...' : 'Retrain Model Now'}</span>
          </button>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSave}
          disabled={saving}
          className="w-full sm:w-auto flex items-center justify-center space-x-2 px-6 py-3 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
        >
          <FiSave className="flex-shrink-0" />
          <span>{saving ? 'Saving...' : 'Save Settings'}</span>
        </button>
      </div>
    </div>
  );
};

export default Settings;
