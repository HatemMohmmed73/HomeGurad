import { useAuthStore } from '../store/authStore';

class WebSocketService {
  private alertSocket: WebSocket | null = null;
  private deviceSocket: WebSocket | null = null;
  private alertReconnectInterval: NodeJS.Timeout | null = null;
  private deviceReconnectInterval: NodeJS.Timeout | null = null;

  private getWebSocketUrl(path: string): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const token = useAuthStore.getState().accessToken;
    return `${protocol}//${host}${path}?token=${token}`;
  }

  connectAlerts(onAlert: (data: any) => void) {
    if (this.alertSocket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Close existing connection if any
    if (this.alertSocket) {
      this.alertSocket.close();
    }

    const url = this.getWebSocketUrl('/ws/alerts');
    this.alertSocket = new WebSocket(url);

    this.alertSocket.onopen = () => {
        console.log('✅ Connected to alerts WebSocket');
      if (this.alertReconnectInterval) {
        clearInterval(this.alertReconnectInterval);
        this.alertReconnectInterval = null;
      }
    };

    this.alertSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        // Handle both direct alert messages and structured messages
        if (message.type === 'new_alert') {
          onAlert(message);
        } else if (message.data && message.data.alert_id) {
          // Handle direct alert data
          onAlert({ type: 'new_alert', data: message.data });
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.alertSocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.alertSocket.onclose = () => {
        console.log('❌ Disconnected from alerts WebSocket');
      // Attempt to reconnect after 5 seconds
      if (!this.alertReconnectInterval) {
        this.alertReconnectInterval = setInterval(() => {
          if (this.alertSocket?.readyState !== WebSocket.OPEN) {
            this.connectAlerts(onAlert);
          }
        }, 5000);
    }
    };
  }

  connectDevices(onDeviceUpdate: (data: any) => void) {
    if (this.deviceSocket?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    // Close existing connection if any
    if (this.deviceSocket) {
      this.deviceSocket.close();
    }

    const url = this.getWebSocketUrl('/ws/devices');
    this.deviceSocket = new WebSocket(url);

    this.deviceSocket.onopen = () => {
        console.log('✅ Connected to devices WebSocket');
      if (this.deviceReconnectInterval) {
        clearInterval(this.deviceReconnectInterval);
        this.deviceReconnectInterval = null;
      }
    };

    this.deviceSocket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === 'device_update') {
          onDeviceUpdate(message);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    this.deviceSocket.onerror = (error) => {
      console.error('❌ WebSocket error:', error);
    };

    this.deviceSocket.onclose = () => {
        console.log('❌ Disconnected from devices WebSocket');
      // Attempt to reconnect after 5 seconds
      if (!this.deviceReconnectInterval) {
        this.deviceReconnectInterval = setInterval(() => {
          if (this.deviceSocket?.readyState !== WebSocket.OPEN) {
            this.connectDevices(onDeviceUpdate);
          }
        }, 5000);
    }
    };
  }

  disconnectAlerts() {
    if (this.alertReconnectInterval) {
      clearInterval(this.alertReconnectInterval);
      this.alertReconnectInterval = null;
    }
    if (this.alertSocket) {
      this.alertSocket.close();
      this.alertSocket = null;
    }
  }

  disconnectDevices() {
    if (this.deviceReconnectInterval) {
      clearInterval(this.deviceReconnectInterval);
      this.deviceReconnectInterval = null;
    }
    if (this.deviceSocket) {
      this.deviceSocket.close();
      this.deviceSocket = null;
    }
  }

  disconnectAll() {
    this.disconnectAlerts();
    this.disconnectDevices();
  }
}

export default new WebSocketService();
