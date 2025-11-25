"""
WebSocket Connection Manager for Real-time Communication
"""
from fastapi import WebSocket
from typing import List, Dict
import json


class WebSocketManager:
    """Manages WebSocket connections for different channels"""
    
    def __init__(self):
        # Dictionary to store connections by channel
        self.active_connections: Dict[str, List[WebSocket]] = {
            "alerts": [],
            "devices": []
        }
    
    async def connect(self, websocket: WebSocket, channel: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)
        print(f"✅ WebSocket connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        """Remove a WebSocket connection"""
        if channel in self.active_connections:
            if websocket in self.active_connections[channel]:
                self.active_connections[channel].remove(websocket)
                print(f"❌ WebSocket disconnected from channel: {channel}")
    
    async def broadcast_to_channel(self, channel: str, message: dict):
        """Broadcast message to all connections in a channel"""
        if channel not in self.active_connections:
            return
        
        disconnected = []
        for connection in self.active_connections[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error sending to websocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected websockets
        for conn in disconnected:
            self.disconnect(conn, channel)
    
    async def send_alert(self, alert_data: dict):
        """Send alert to all connected clients"""
        await self.broadcast_to_channel("alerts", {
            "type": "new_alert",
            "data": alert_data
        })
    
    async def send_device_update(self, device_data: dict):
        """Send device status update to all connected clients"""
        await self.broadcast_to_channel("devices", {
            "type": "device_update",
            "data": device_data
        })
    
    def get_active_connections_count(self, channel: str = None) -> int:
        """Get count of active connections"""
        if channel:
            return len(self.active_connections.get(channel, []))
        return sum(len(conns) for conns in self.active_connections.values())


# Global instance
websocket_manager = WebSocketManager()

