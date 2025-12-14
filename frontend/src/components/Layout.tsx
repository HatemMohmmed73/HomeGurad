import { useState, useEffect } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { 
  FiHome, 
  FiShield, 
  FiAlertTriangle, 
  FiLogOut,
  FiMenu,
  FiX
} from 'react-icons/fi';
import { useAuthStore } from '../store/authStore';
import websocket from '../services/websocket';
import AlertPopup from './AlertPopup';
import { Alert } from '../types';

const Layout = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [newAlert, setNewAlert] = useState<Alert | null>(null);

  const navItems = [
    { path: '/', icon: FiHome, label: 'Dashboard' },
    { path: '/alerts', icon: FiAlertTriangle, label: 'Alerts' },
  ];

  useEffect(() => {
    // Global WebSocket connection for Alerts
    if (user) {
      websocket.connectAlerts((message) => {
        if (message.type === 'new_alert' && message.data) {
          const alertData = message.data;
          
          const newAlertObj: Alert = {
            _id: alertData.alert_id || alertData.device_ip,
            device_id: alertData.device_ip, // Assuming IP is ID for now or it's passed
            device_ip: alertData.device_ip,
            device_mac: alertData.device_mac || alertData.device_ip,
            device_name: alertData.device_name || alertData.device_ip,
            alert_type: 'anomaly',
            severity: alertData.severity || 'medium',
            timestamp: alertData.timestamp ? new Date(alertData.timestamp * 1000).toISOString() : new Date().toISOString(),
            reason: alertData.reason || 'Anomalous activity detected',
            details: {},
            action_taken: alertData.action_taken || null,
            acknowledged: alertData.status === 'acknowledged'
          };
          
          setNewAlert(newAlertObj);
        }
      });
    }

    return () => {
      // Don't disconnect here if we want persistence, but for cleanup it's good.
      // Since Layout unmounts only on logout/close, it's fine.
      websocket.disconnectAlerts();
    };
  }, [user]);

  const isActive = (path: string) => location.pathname === path;

  const handleLogout = () => {
    websocket.disconnectAll();
    logout();
    navigate('/login', { replace: true });
  };

  const closeSidebar = () => {
    setSidebarOpen(false);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Alert Popup */}
      <AlertPopup 
        alert={newAlert} 
        onClose={() => setNewAlert(null)}
        onViewDetails={() => navigate('/alerts')} 
      />

      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 bg-white shadow-sm z-30 flex items-center justify-between px-4 py-3">
        <div className="flex items-center space-x-2">
          <FiShield className="text-2xl text-blue-600" />
          <h1 className="text-lg font-bold text-gray-800">HomeGuard</h1>
        </div>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
        >
          {sidebarOpen ? <FiX className="text-xl" /> : <FiMenu className="text-xl" />}
        </button>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black bg-opacity-50 z-20"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:fixed left-0 top-0 h-screen w-64 bg-white shadow-lg z-20 transition-transform duration-300 lg:translate-x-0 ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex flex-col h-full">
          {/* Logo (desktop only) */}
          <div className="hidden lg:block p-6 border-b">
            <div className="flex items-center space-x-2">
              <FiShield className="text-3xl text-blue-600" />
              <div>
                <h1 className="text-xl font-bold text-gray-800">HomeGuard</h1>
                <p className="text-xs text-gray-500">IoT Security</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 pt-16 lg:pt-4">
            <ul className="space-y-2">
              {navItems.map((item) => (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={closeSidebar}
                    className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                      isActive(item.path)
                        ? 'bg-blue-50 text-blue-600 font-medium'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    <item.icon className="text-xl flex-shrink-0" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </nav>

          {/* User Info */}
          <div className="p-4 border-t">
            <div className="flex items-center justify-between gap-2">
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">
                  {user?.full_name || user?.email}
                </p>
                <p className="text-xs text-gray-500 capitalize">{user?.role}</p>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
                title="Logout"
              >
                <FiLogOut className="text-lg" />
              </button>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64">
        <div className="mt-16 lg:mt-0 min-h-screen flex flex-col">
          <div className="flex-1 p-4 sm:p-6 lg:p-8">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
};

export default Layout;
