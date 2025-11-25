import { io, Socket } from 'socket.io-client';

class WebSocketService {
  private alertSocket: Socket | null = null;
  private deviceSocket: Socket | null = null;

  connectAlerts(onAlert: (data: any) => void) {
    if (!this.alertSocket) {
      this.alertSocket = io('/ws/alerts', {
        transports: ['websocket'],
      });

      this.alertSocket.on('connect', () => {
        console.log('✅ Connected to alerts WebSocket');
      });

      this.alertSocket.on('new_alert', (data) => {
        onAlert(data);
      });

      this.alertSocket.on('disconnect', () => {
        console.log('❌ Disconnected from alerts WebSocket');
      });
    }
  }

  connectDevices(onDeviceUpdate: (data: any) => void) {
    if (!this.deviceSocket) {
      this.deviceSocket = io('/ws/devices', {
        transports: ['websocket'],
      });

      this.deviceSocket.on('connect', () => {
        console.log('✅ Connected to devices WebSocket');
      });

      this.deviceSocket.on('device_update', (data) => {
        onDeviceUpdate(data);
      });

      this.deviceSocket.on('disconnect', () => {
        console.log('❌ Disconnected from devices WebSocket');
      });
    }
  }

  disconnectAlerts() {
    if (this.alertSocket) {
      this.alertSocket.disconnect();
      this.alertSocket = null;
    }
  }

  disconnectDevices() {
    if (this.deviceSocket) {
      this.deviceSocket.disconnect();
      this.deviceSocket = null;
    }
  }

  disconnectAll() {
    this.disconnectAlerts();
    this.disconnectDevices();
  }
}

export default new WebSocketService();

