"""
HomeGuard - Per-Device Behavioral Firewall for Smart Homes
FastAPI Backend with OpenAPI/Swagger Documentation
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

from database.mongodb import connect_db, close_db
from api.routes import auth, devices, alerts, settings_api, websocket as websocket_routes, push
from core.alert_monitor import alert_monitor

# ============= Lifespan Context Manager =============

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage app startup and shutdown"""
    # Startup
    try:
        await connect_db()
        # Start alert monitoring (non-blocking, don't fail if it errors)
        try:
            await alert_monitor.start()
        except Exception as e:
            print(f"⚠️  Warning: Alert monitoring failed to start: {e}")
            # Don't crash the app if monitoring fails
    except Exception as e:
        print(f"❌ Error during startup: {e}")
        import traceback
        traceback.print_exc()
        raise
    yield
    # Shutdown
    alert_monitor.monitoring = False
    await close_db()


# ============= FastAPI App =============

app = FastAPI(
    title="HomeGuard API",
    description="""
🛡️ **HomeGuard: Per-Device Behavioral Firewall for Smart Homes**

A comprehensive AI-powered network monitoring and device management system for smart homes.
Detects anomalies in device behavior using machine learning and provides real-time alerts.

## 🎯 Core Features:
- **Device Management**: Monitor and control IoT devices in your smart home
- **Anomaly Detection**: ML-based behavioral analysis using Isolation Forest
- **Real-time Alerts**: Get notified immediately about suspicious device activity
- **Firewall Control**: Block malicious devices using nftables
- **User Management**: Multi-user support with role-based access control
- **System Settings**: Configure detection thresholds and monitoring options

## 🔐 Authentication:
All endpoints (except /health and /docs) require JWT Bearer authentication.
Use `/api/auth/login` to get access and refresh tokens.

## 📊 Response Format:
All successful responses follow standard JSON format with proper HTTP status codes.
Error responses include detailed error messages for debugging.

## 🚀 Quick Start:
1. Register or login via `/api/auth/register` or `/api/auth/login`
2. Get your user profile via `/api/auth/me`
3. Manage devices via `/api/devices`
4. Monitor alerts via `/api/alerts`
5. Run ML inference via `/api/model/inference`
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    contact={
        "name": "HomeGuard Support",
        "url": "https://homeguard.local",
        "email": "support@homeguard.local",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# ============= CORS Configuration =============

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# ============= API Routes with Tags =============

app.include_router(
    auth.router,
    prefix="/api/auth",
    tags=["🔐 Authentication"],
    responses={
        401: {"description": "Unauthorized - Invalid credentials or token"},
        400: {"description": "Bad Request - Invalid input"},
    }
)

app.include_router(
    devices.router,
    prefix="/api/devices",
    tags=["📱 Device Management"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Device not found"},
        422: {"description": "Unprocessable Entity"},
    }
)

app.include_router(
    alerts.router,
    prefix="/api/alerts",
    tags=["🚨 Alerts & Notifications"],
    responses={
        401: {"description": "Unauthorized"},
        404: {"description": "Alert not found"},
    }
)


app.include_router(
    settings_api.router,
    prefix="/api/settings",
    tags=["⚙️ System Settings"],
    responses={
        401: {"description": "Unauthorized"},
    }
)

# WebSocket routes (no prefix, direct paths)
app.include_router(websocket_routes.router)

# Push notification routes
app.include_router(
    push.router,
    prefix="/api/push",
    tags=["📱 Push Notifications"],
    responses={
        401: {"description": "Unauthorized"},
    }
)


# ============= Health Check Endpoint =============

@app.get(
    "/health",
    tags=["❤️ Health Check"],
    summary="Health Check Endpoint",
    description="Check if the API is running and healthy",
    response_description="Health status",
)
async def health_check():
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "environment": "production",
        "version": "1.0.0",
        "service": "HomeGuard API"
    }


@app.get("/", tags=["📄 Documentation"])
async def root():
    """Root endpoint - redirects to API documentation"""
    return {
        "message": "Welcome to HomeGuard API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health"
    }


# ============= Custom OpenAPI Schema =============

def custom_openapi():
    """Generate custom OpenAPI schema with enhanced documentation"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="HomeGuard API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
        tags=[
            {
                "name": "🔐 Authentication",
                "description": "User registration, login, and profile management endpoints",
                "externalDocs": {
                    "description": "Learn more about JWT authentication",
                    "url": "https://jwt.io/"
                }
            },
            {
                "name": "📱 Device Management",
                "description": "CRUD operations for IoT devices connected to the network",
                "externalDocs": {
                    "description": "IoT Device Standards",
                    "url": "https://www.iot.org/"
                }
            },
            {
                "name": "🚨 Alerts & Notifications",
                "description": "Retrieve and manage security alerts from anomaly detection",
                "externalDocs": {
                    "description": "Security Alert Types",
                    "url": "https://www.issa.org/"
                }
            },
            {
                "name": "🤖 ML Model & Inference",
                "description": "Machine learning model status and anomaly inference endpoints",
                "externalDocs": {
                    "description": "Isolation Forest Algorithm",
                    "url": "https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html"
                }
            },
            {
                "name": "⚙️ System Settings",
                "description": "Configure HomeGuard system behavior and detection parameters",
            },
            {
                "name": "❤️ Health Check",
                "description": "Service health and status monitoring",
            },
            {
                "name": "📄 Documentation",
                "description": "API documentation and metadata endpoints",
            },
            {
                "name": "🛡️ Security",
                "description": "Security-related endpoints for managing firewall rules and alerts",
            }
        ],
    )
    
    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "BearerTokenAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT Bearer token for authentication",
        }
    }
    
    # Add security to all endpoints except health and docs
    for path, methods in openapi_schema["paths"].items():
        if path not in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            for method, operation in methods.items():
                if isinstance(operation, dict) and "security" not in operation:
                    operation["security"] = [{"BearerTokenAuth": []}]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# ============= Event Handlers =============

@app.on_event("startup")
async def startup_event():
    """Startup event"""
    print("🚀 HomeGuard API is starting up...")


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event"""
    print("🛑 HomeGuard API is shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

