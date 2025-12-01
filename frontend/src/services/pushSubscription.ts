/**
 * Web Push Subscription Service
 * Handles push notification subscription and registration
 */
import api from './api';

class PushSubscriptionService {
  private registration: ServiceWorkerRegistration | null = null;
  private vapidPublicKey: string | null = null;

  /**
   * Initialize push subscription service
   */
  async initialize(): Promise<boolean> {
    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
      console.warn('Push notifications are not supported in this browser');
      return false;
    }

    try {
      // Register service worker
      this.registration = await navigator.serviceWorker.register('/sw.js', {
        scope: '/'
      });
      console.log('✅ Service Worker registered');

      // Get VAPID public key from server
      await this.loadVapidKey();

      return true;
    } catch (error) {
      console.error('Error initializing push service:', error);
      return false;
    }
  }

  /**
   * Load VAPID public key from server
   */
  async loadVapidKey(): Promise<void> {
    try {
      const response = await api.get('/push/vapid-public-key');
      this.vapidPublicKey = response.data.public_key;
    } catch (error) {
      console.error('Error loading VAPID key:', error);
    }
  }

  /**
   * Request notification permission
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      return 'denied';
    }
    return await Notification.requestPermission();
  }

  /**
   * Subscribe to push notifications
   */
  async subscribe(): Promise<boolean> {
    if (!this.registration || !this.vapidPublicKey) {
      console.error('Service Worker or VAPID key not available');
      return false;
    }

    try {
      // Request permission
      const permission = await this.requestPermission();
      if (permission !== 'granted') {
        console.warn('Notification permission denied');
        return false;
      }

      // Subscribe to push service
      const subscription = await this.registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
      });

      // Send subscription to server
      const subscriptionData = {
        endpoint: subscription.endpoint,
        keys: {
          p256dh: this.arrayBufferToBase64(subscription.getKey('p256dh')!),
          auth: this.arrayBufferToBase64(subscription.getKey('auth')!)
        },
        user_agent: navigator.userAgent,
        device_info: {
          platform: navigator.platform,
          language: navigator.language
        }
      };

      await api.post('/push/subscribe', subscriptionData);
      console.log('✅ Push subscription successful');
      return true;
    } catch (error) {
      console.error('Error subscribing to push:', error);
      return false;
    }
  }

  /**
   * Unsubscribe from push notifications
   */
  async unsubscribe(): Promise<boolean> {
    if (!this.registration) {
      return false;
    }

    try {
      const subscription = await this.registration.pushManager.getSubscription();
      if (subscription) {
        await subscription.unsubscribe();
        await api.post('/push/unsubscribe', { endpoint: subscription.endpoint });
        console.log('✅ Push unsubscription successful');
        return true;
      }
      return false;
    } catch (error) {
      console.error('Error unsubscribing from push:', error);
      return false;
    }
  }

  /**
   * Check if user is subscribed
   */
  async isSubscribed(): Promise<boolean> {
    if (!this.registration) {
      return false;
    }

    const subscription = await this.registration.pushManager.getSubscription();
    return subscription !== null;
  }

  /**
   * Convert VAPID key from base64url to Uint8Array
   */
  private urlBase64ToUint8Array(base64String: string): Uint8Array {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  /**
   * Convert ArrayBuffer to base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
  }
}

export default new PushSubscriptionService();

