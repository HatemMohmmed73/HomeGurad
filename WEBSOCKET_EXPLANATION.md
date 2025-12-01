# WebSocket Implementation Explanation

## What is WebSocket?

WebSocket is a communication protocol that provides **full-duplex communication** over a single TCP connection. Unlike HTTP (which is request-response), WebSocket allows the server to **push data to the client** in real-time without the client needing to request it.

### Key Differences:

| HTTP/REST API | WebSocket |
|---------------|-----------|
| Request → Response | Persistent connection |
| Client must poll for updates | Server pushes updates |
| One-way communication | Two-way communication |
| Higher latency | Lower latency |
| More overhead per request | Less overhead |

## How It Works in HomeGuard

### Architecture Flow:

```
Frontend (React)  ←→  WebSocket Connection  ←→  Backend (FastAPI)
     ↓                                              ↓
Dashboard UI                              WebSocketManager
     ↓                                              ↓
Receives real-time updates              Broadcasts to all clients
```

### 1. Backend Implementation (`backend/core/websocket_manager.py`)

**WebSocketManager Class:**
- Manages multiple WebSocket connections
- Organizes connections by **channels** (alerts, devices)
- Broadcasts messages to all connected clients in a channel

```python
class WebSocketManager:
    def __init__(self):
        # Store connections by channel
        self.active_connections = {
            "alerts": [],    # List of WebSocket connections
            "devices": []    # List of WebSocket connections
        }
    
    async def connect(self, websocket, channel):
        """Accept and register a new connection"""
        await websocket.accept()
        self.active_connections[channel].append(websocket)
    
    async def broadcast_to_channel(self, channel, message):
        """Send message to all connections in a channel"""
        for connection in self.active_connections[channel]:
            await connection.send_json(message)
```

### 2. WebSocket Endpoints (`backend/api/routes/websocket.py`)

**Two endpoints:**
- `/ws/alerts` - For real-time alert notifications
- `/ws/devices` - For real-time device status updates

**Connection Process:**
1. Client connects to `/ws/alerts` or `/ws/devices`
2. Server verifies JWT token (authentication)
3. Server accepts connection and adds to channel
4. Connection stays open for real-time communication
5. Server can send messages anytime
6. Client receives messages automatically

```python
@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket, token: str = None):
    # 1. Verify authentication
    user = await verify_websocket_token(websocket, token)
    
    # 2. Connect to alerts channel
    await websocket_manager.connect(websocket, "alerts")
    
    # 3. Keep connection alive
    try:
        while True:
            data = await websocket.receive_text()
            # Process messages if needed
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "alerts")
```

### 3. Triggering WebSocket Messages

When a device is blocked/unblocked, the backend sends updates:

```python
# In devices.py
async def block_device(...):
    # ... block device logic ...
    
    # Send update via WebSocket
    await websocket_manager.send_device_update(device)
```

This automatically notifies **all connected clients** in real-time!

### 4. Frontend Implementation (`frontend/src/services/websocket.ts`)

**WebSocketService Class:**
- Manages WebSocket connections from the browser
- Handles reconnection automatically
- Parses incoming messages and triggers callbacks

```typescript
class WebSocketService {
  connectAlerts(onAlert: (data: any) => void) {
    // 1. Get JWT token from auth store
    const token = useAuthStore.getState().accessToken;
    
    // 2. Create WebSocket connection
    const url = `ws://host/ws/alerts?token=${token}`;
    this.alertSocket = new WebSocket(url);
    
    // 3. Handle incoming messages
    this.alertSocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'new_alert') {
        onAlert(message); // Callback to update UI
      }
    };
  }
}
```

### 5. Using WebSocket in React Components

```typescript
// In Dashboard.tsx
useEffect(() => {
  // Connect to WebSocket when component mounts
  websocket.connectAlerts((data) => {
    // Update UI when new alert arrives
    toast.warning(`New Alert: ${data.data.reason}`);
    setRecentAlerts((prev) => [data.data, ...prev.slice(0, 4)]);
  });
  
  websocket.connectDevices((data) => {
    // Update device status in real-time
    updateDevice(data.data);
  });
  
  // Cleanup on unmount
  return () => {
    websocket.disconnectAll();
  };
}, []);
```

## Message Flow Example

**Scenario: Device is blocked**

1. **Admin clicks "Block Device"** in dashboard
2. **Frontend** sends `POST /api/devices/{id}/block`
3. **Backend** processes request and blocks device
4. **Backend** calls `websocket_manager.send_device_update(device)`
5. **WebSocketManager** broadcasts to all clients in "devices" channel
6. **All connected dashboards** receive update instantly
7. **UI updates** automatically without page refresh!

## Benefits

✅ **Real-time Updates**: No need to poll API every few seconds  
✅ **Lower Latency**: Instant notifications  
✅ **Efficient**: Single persistent connection  
✅ **Scalable**: Can handle multiple clients per channel  
✅ **Automatic Reconnection**: Frontend reconnects if connection drops  

## Security

- **JWT Authentication**: Token required to connect
- **Token Validation**: Server verifies token before accepting connection
- **Channel Isolation**: Alerts and devices are separate channels

## Current Status

✅ WebSocket endpoints implemented  
✅ Frontend WebSocket service implemented  
✅ Automatic reconnection on disconnect  
✅ JWT authentication for WebSocket connections  
✅ Real-time device and alert updates  

Note: Currently, the system also uses **polling (5-second intervals)** as a fallback to ensure data is always up-to-date, even if WebSocket connection fails.

