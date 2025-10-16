from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Bollisetti Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database Configuration
    DATABASE_URL: str = "postgresql://postgres.mqvtfijggstbztaxmonu:Mohan@2005@aws-1-ap-south-1.pooler.supabase.com:6543/postgres?pgbouncer=true"
    DIRECT_URL: str = "postgresql://postgres.mqvtfijggstbztaxmonu:Mohan@2005@aws-1-ap-south-1.pooler.supabase.com:5432/postgres"

    # Supabase Configuration
    SUPABASE_URL: str = "https://mqvtfijggstbztaxmonu.supabase.co"
    SUPABASE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1xdnRmaWpnZ3N0Ynp0YXhtb251Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTk5ODQzMzksImV4cCI6MjA3NTU2MDMzOX0.VzkTbGHO3dXv374jpcNV4osYNLwov1S94ShhtWqloXs"
    SUPABASE_SERVICE_ROLE_KEY: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1xdnRmaWpnZ3N0Ynp0YXhtb251Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1OTk4NDMzOSwiZXhwIjoyMDc1NTYwMzM5fQ.xTfiNf9ZVmLA8OK8yqy0zFF34XwqEfZ4idJcQVMIK-0"
    
    # JWT Configuration
    SECRET_KEY: str = "oi8b9RRvAbVawdPOxPKeUnu_9QAmqTlLk7lGhpWifZU"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Configuration
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080", 
        "http://localhost:19006"
    ]
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads"
    
    # ZenStack Service Configuration
    zenstack_service_url: str = os.getenv("ZENSTACK_SERVICE_URL", "https://bolisetti-zenstack.onrender.com")
    zenstack_service_port: int = 3001
    
    class Config:
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
