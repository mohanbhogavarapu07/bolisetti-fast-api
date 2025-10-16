import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
from app.config import settings
from app.zenstack_client import zenstack_client

async def save_upload_file(upload_file: UploadFile, folder: str = "uploads", user_token: Optional[str] = None) -> str:
    """Save uploaded file to Supabase Storage via ZenStack"""
    try:
        # Generate unique filename
        file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await upload_file.read()
        
        # Upload via ZenStack to Supabase Storage
        response = await zenstack_client.upload_file(
            file_data=file_content,
            filename=unique_filename,
            content_type=upload_file.content_type or "application/octet-stream",
            folder=folder,
            user_token=user_token
        )
        
        if response and response.get("success"):
            return response.get("url")
        else:
            raise Exception("Upload failed")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

async def delete_file(file_url: str, user_token: Optional[str] = None) -> bool:
    """Delete file from Supabase Storage via ZenStack"""
    try:
        # Extract file path from URL
        if "bolisetti-files/" in file_url:
            file_path = file_url.split("bolisetti-files/")[1]
        else:
            file_path = file_url.split("/")[-1]
        
        return await zenstack_client.delete_file(file_path, user_token)
    except Exception as e:
        print(f"Failed to delete file: {str(e)}")
        return False

def validate_file_size(file: UploadFile) -> bool:
    """Validate file size"""
    if file.size and file.size > settings.max_file_size:
        return False
    return True

def validate_file_type(file: UploadFile, allowed_types: list) -> bool:
    """Validate file type"""
    if file.content_type not in allowed_types:
        return False
    return True

# Common file type validators
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"]
ALLOWED_VIDEO_TYPES = ["video/mp4", "video/avi", "video/mov", "video/wmv"]
ALLOWED_DOCUMENT_TYPES = ["application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
