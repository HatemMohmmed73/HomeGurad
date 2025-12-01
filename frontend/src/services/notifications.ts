/**
 * Browser Notification Service
 * Handles browser notifications that work even when the tab is not active
 */

class NotificationService {
  private permission: NotificationPermission = 'default';

  /**
   * Request permission for browser notifications
   */
  async requestPermission(): Promise<boolean> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return false;
    }

    if (this.permission === 'granted') {
      return true;
    }

    if (this.permission === 'default') {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      return permission === 'granted';
    }

    return false;
  }

  /**
   * Check if notifications are supported and permitted
   */
  isSupported(): boolean {
    return 'Notification' in window;
  }

  /**
   * Check if permission is granted
   */
  hasPermission(): boolean {
    if (!('Notification' in window)) {
      return false;
    }
    return Notification.permission === 'granted';
  }

  /**
   * Show a browser notification
   */
  async showNotification(
    title: string,
    options: NotificationOptions = {}
  ): Promise<void> {
    if (!this.hasPermission()) {
      const granted = await this.requestPermission();
      if (!granted) {
        console.warn('Notification permission denied');
        return;
      }
    }

    // Default options
    const defaultOptions: NotificationOptions = {
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      requireInteraction: false,
      ...options,
    };

    // Show notification
    const notification = new Notification(title, defaultOptions);

    // Auto-close after 5 seconds
    setTimeout(() => {
      notification.close();
    }, 5000);

    // Handle click - focus the window
    notification.onclick = () => {
      window.focus();
      notification.close();
    };
  }

  /**
   * Show alert notification
   */
  async showAlertNotification(alert: {
    reason: string;
    device_name?: string;
    severity?: string;
    alert_id?: string;
  }): Promise<void> {
    const severity = alert.severity?.toUpperCase() || 'ALERT';
    const title = `🚨 ${severity} Alert: ${alert.device_name || 'Unknown Device'}`;
    const body = alert.reason;

    // Choose icon based on severity
    let icon = '/favicon.ico';
    if (alert.severity === 'high' || alert.severity === 'critical') {
      icon = '/favicon.ico'; // You can add custom icons later
    }

    await this.showNotification(title, {
      body,
      icon,
      tag: alert.alert_id || 'alert', // Prevent duplicate notifications
      requireInteraction: alert.severity === 'high' || alert.severity === 'critical',
      badge: icon,
    });
  }
}

export default new NotificationService();

