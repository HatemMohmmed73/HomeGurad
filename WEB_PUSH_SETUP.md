# Web Push Notifications - Complete Setup Guide

## ✅ What's Implemented

Your HomeGuard system now supports **Web Push Notifications** that work even when:
- ✅ Browser is **completely closed**
- ✅ User is **away from computer**
- ✅ User logged in from **multiple devices**

## How It Works

### 1. **User Login & Subscription**
```
User logs in → Dashboard loads
     ↓
Service Worker registers
     ↓
User grants permission
     ↓
Push subscription saved to database
     ↓
Device is registered for notifications
```

### 2. **Alert Detection & Notification**
```
Orange Pi Script → Updates alerts.json
     ↓
Alert Monitor detects new alert
     ↓
Backend sends push notification to ALL registered devices
     ↓
User receives notification on ALL devices (even if browser closed)
     ↓
User clicks notification → Browser opens → Dashboard loads
```

## Features

✅ **Multi-Device Support**: User can login from multiple devices, all receive notifications  
✅ **Works When Browser Closed**: Notifications delivered via browser push service  
✅ **Automatic Registration**: Subscribes automatically when user logs in  
✅ **Device Tracking**: Stores device info (browser, platform) for each subscription  
✅ **Auto-Cleanup**: Removes invalid subscriptions automatically  

## Files Created

### Backend:
- `backend/core/push_notifications.py` - Push notification service
- `backend/api/routes/push.py` - Push subscription API endpoints
- `backend/database/models.py` - Added PushSubscription model
- `backend/database/mongodb.py` - Added push_subscriptions collection

### Frontend:
- `frontend/public/sw.js` - Service Worker for handling push events
- `frontend/src/services/pushSubscription.ts` - Push subscription management
- Updated `frontend/src/pages/Dashboard.tsx` - Auto-subscribe on login

## API Endpoints

- `GET /api/push/vapid-public-key` - Get VAPID public key
- `POST /api/push/subscribe` - Subscribe to push notifications
- `POST /api/push/unsubscribe` - Unsubscribe from push notifications
- `GET /api/push/subscriptions` - Get user's subscriptions

## Testing

1. **Login to dashboard** from a device
2. **Grant notification permission** when prompted
3. **Close browser completely**
4. **Add new alert** to `alerts.json` on Orange Pi
5. **Receive notification** on your device (even with browser closed!)
6. **Click notification** → Browser opens → Dashboard loads

## Production Setup

For production, you should:

1. **Generate VAPID keys**:
   ```bash
   python3 -c "from py_vapid import Vapid01; v = Vapid01(); v.generate_keys(); print('Private:', v.private_key); print('Public:', v.public_key)"
   ```

2. **Set environment variable**:
   ```bash
   export VAPID_PRIVATE_KEY="your_private_key_here"
   ```

3. **Update docker-compose.yml** to include VAPID_PRIVATE_KEY

## How It Saves Device Information

When a user logs in:
1. Service Worker registers
2. Push subscription is created
3. Device info is saved:
   - User email
   - Push endpoint
   - Encryption keys
   - Browser user agent
   - Device platform
   - Timestamp

When an alert happens:
1. Backend finds ALL subscriptions for the user
2. Sends push notification to ALL devices
3. All devices receive notification (even if browser closed)

## Current Status

✅ Service Worker created  
✅ Push subscription service implemented  
✅ API endpoints created  
✅ Auto-subscription on login  
✅ Alert monitor sends push notifications  
✅ Multi-device support  

**Ready to test!** 🚀

