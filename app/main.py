from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.routers import auth, users, grievances, schedules, news, projects, schedule_events, media, notifications, upload, constituencies, departments, admin_auth, admin_management

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend API for Bollisetti Government Services App",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this properly for production
)

# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(grievances.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(news.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(schedule_events.router, prefix="/api")
app.include_router(media.router, prefix="/api")
app.include_router(notifications.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(constituencies.router, prefix="/api")
app.include_router(departments.router, prefix="/api")
app.include_router(admin_auth.router, prefix="/api")
app.include_router(admin_management.router, prefix="/api")

# Health check endpoint
@app.get("/")
async def root():
    return {
        "message": "Bollisetti Backend API",
        "version": settings.app_version,
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": settings.app_version}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )
