from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # App Configuration
    app_name: str = "Bollisetti Backend"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    DIRECT_URL: str = os.getenv("DIRECT_URL", "")

    # Supabase Configuration
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_KEY: str = os.getenv("SUPABASE_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Configuration - handled manually to avoid Pydantic JSON parsing
    
    # File Upload Configuration
    max_file_size: int = 10485760  # 10MB
    upload_dir: str = "uploads"
    
    # ZenStack Service Configuration
    zenstack_service_url: str = os.getenv("ZENSTACK_SERVICE_URL", "http://localhost:3001")
    zenstack_service_port: int = 3001
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle CORS origins manually to avoid Pydantic JSON parsing issues
        if os.getenv("ALLOWED_ORIGINS"):
            object.__setattr__(self, 'allowed_origins', os.getenv("ALLOWED_ORIGINS").split(","))
        else:
            object.__setattr__(self, 'allowed_origins', [
                "http://localhost:3000",
                "http://localhost:8080", 
                "http://localhost:19006"
                "http://localhost:5174",
                "http://localhost:5173"
            ])
    
    class Config:
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.upload_dir, exist_ok=True)
