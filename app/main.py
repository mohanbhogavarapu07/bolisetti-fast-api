from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.config import settings
from app.routers import grievances, news, projects, schedule_events, media, notifications, constituencies, departments, admin_auth, user_auth

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Bollisetti Backend API...")
    try:
        from app.database import db_client
        # Test database connection with a simple query
        async with db_client:
            # Try to execute a simple query to test connection
            await db_client.prisma.user.find_first()
            print("✅ Database connection successful!")
            print("📊 Database is ready for operations")
        print("🎉 Backend API started successfully!")
    except Exception as e:
        if "Already connected" in str(e):
            print("✅ Database connection successful! (Already connected)")
            print("📊 Database is ready for operations")
            print("🎉 Backend API started successfully!")
        else:
            print(f"❌ Database connection failed: {str(e)}")
            print("⚠️  Server starting without database connection")
    
    yield
    
    # Shutdown
    print("🔄 Shutting down backend API...")
    try:
        from app.database import db_client
        async with db_client:
            await db_client.prisma.disconnect()
        print("✅ Database connection closed successfully")
    except Exception as e:
        print(f"⚠️  Error closing database connection: {str(e)}")
    print("👋 Backend API shutdown complete")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    ## Bollisetti Government Services API
    
    A unified, entity-based API for government services with role-based access control.
    
    ### Authentication
    - **User Authentication**: JWT tokens for regular users
    - **Admin Authentication**: JWT tokens for admin users
    
    ### Role-Based Access
    - **Public**: No authentication required (projects, news, events)
    - **User**: Authenticated users can access their own data
    - **Admin**: Full access to all resources and management functions
    
    ### Entity-Based Routes
    - **Users** (`/api/users`): User management with admin controls
    - **Grievances** (`/api/grievances`): Grievance system with admin status updates
    - **News** (`/api/news`): News articles with admin CRUD operations
    - **Projects** (`/api/projects`): Development projects (public read, admin write)
    - **Events** (`/api/schedule_events`): Schedule events (public read, admin write)
    - **Media** (`/api/media`): Media management
    - **Notifications** (`/api/notifications`): User notifications
    - **Constituencies** (`/api/constituencies`): Constituency data
    - **Departments** (`/api/departments`): Department data
    """,
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

# Include authentication routers
app.include_router(user_auth.router, prefix="/api", tags=["👤 Users"])
app.include_router(admin_auth.router, prefix="/api", tags=["🔐 Admin Authentication"])

# Include unified entity-based routers with role-based access
app.include_router(grievances.router, prefix="/api", tags=["📝 Grievances"])
app.include_router(news.router, prefix="/api", tags=["📰 News"])
app.include_router(projects.router, prefix="/api", tags=["🏗️ Projects"])
app.include_router(schedule_events.router, prefix="/api", tags=["📅 Events"])
app.include_router(media.router, prefix="/api", tags=["📁 Media"])
app.include_router(notifications.router, prefix="/api", tags=["🔔 Notifications"])
app.include_router(constituencies.router, prefix="/api", tags=["🏛️ Constituencies"])
app.include_router(departments.router, prefix="/api", tags=["🏢 Departments"])

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
