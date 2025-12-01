"""
WebSocket API Routes for Real-time Communication
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.websocket_manager import websocket_manager
from core.security import decode_token

router = APIRouter()
security = HTTPBearer()


async def verify_websocket_token(websocket: WebSocket, token: str = None):
    """Verify JWT token for WebSocket connection"""
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return None
    
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token[7:]
        
        from jose import JWTError, jwt
        from config import settings
        
        # Decode token directly (don't use decode_token as it raises HTTPException)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("sub")
        if not email:
            await websocket.close(code=1008, reason="Invalid token")
            return None
        return payload
    except Exception as e:
        await websocket.close(code=1008, reason="Invalid token")
        return None


@router.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time alerts
    
    Connect with: ws://host/ws/alerts?token=YOUR_JWT_TOKEN
    """
    # Get token from query parameter
    token = websocket.query_params.get("token")
    
    # Verify authentication
    user = await verify_websocket_token(websocket, token)
    if not user:
        return
    
    # Connect to alerts channel
    await websocket_manager.connect(websocket, "alerts")
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or process message if needed
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "alerts")
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, "alerts")


@router.websocket("/ws/devices")
async def websocket_devices(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time device updates
    
    Connect with: ws://host/ws/devices?token=YOUR_JWT_TOKEN
    """
    # Get token from query parameter
    token = websocket.query_params.get("token")
    
    # Verify authentication
    user = await verify_websocket_token(websocket, token)
    if not user:
        return
    
    # Connect to devices channel
    await websocket_manager.connect(websocket, "devices")
    
    try:
        while True:
            # Keep connection alive and listen for messages
            data = await websocket.receive_text()
            # Echo back or process message if needed
            await websocket.send_json({"type": "pong", "message": "Connection alive"})
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, "devices")
    except Exception as e:
        print(f"WebSocket error: {e}")
        websocket_manager.disconnect(websocket, "devices")

