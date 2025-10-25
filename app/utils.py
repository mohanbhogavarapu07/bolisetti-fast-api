import os
import uuid
import hashlib
from typing import Optional, Dict, Any
from fastapi import UploadFile, HTTPException
from app.config import settings
# Removed zenstack_client import - using direct Supabase storage

async def save_upload_file(upload_file: UploadFile, folder: str = "uploads", user_token: Optional[str] = None) -> str:
    """Save uploaded file directly to Supabase Storage"""
    try:
        import httpx
        from app.config import settings
        
        # Generate unique filename
        file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".jpg"
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Read file content
        file_content = await upload_file.read()
        
        # Upload directly to Supabase Storage
        file_path = f"{folder}/{unique_filename}"
        url = f"{settings.SUPABASE_URL}/storage/v1/object/bolisetti-files/{file_path}"
        
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": upload_file.content_type or "application/octet-stream"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, content=file_content, headers=headers)
            
            if response.status_code == 200:
                # Return the public URL
                return f"{settings.SUPABASE_URL}/storage/v1/object/public/bolisetti-files/{file_path}"
            else:
                raise Exception(f"Supabase upload failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(e)}"
        )

def generate_unique_media_code(entity_type: str, entity_id: str = None) -> str:
    """Generate unique code for media based on entity type and ID"""
    timestamp = str(int(uuid.uuid4().time_low))
    random_part = str(uuid.uuid4().hex)[:8]
    
    if entity_id:
        # Create hash from entity_id for consistency
        entity_hash = hashlib.md5(entity_id.encode()).hexdigest()[:6]
        return f"{entity_type}_{entity_hash}_{timestamp}_{random_part}".upper()
    else:
        return f"{entity_type}_{timestamp}_{random_part}".upper()

async def upload_project_image(
    upload_file: UploadFile, 
    project_id: str, 
    user_token: Optional[str] = None
) -> Dict[str, Any]:
    """Upload project image and create media record with unique code"""
    try:
        # Generate unique code for this project image
        unique_code = generate_unique_media_code("PROJECT", project_id)
        
        # Generate unique filename with project prefix
        file_extension = os.path.splitext(upload_file.filename)[1] if upload_file.filename else ".jpg"
        unique_filename = f"project_{project_id}_{unique_code}{file_extension}"
        
        # Read file content
        file_content = await upload_file.read()
        
        # Upload directly to Supabase Storage
        file_path = f"projects/{unique_filename}"
        url = f"{settings.SUPABASE_URL}/storage/v1/object/bolisetti-files/{file_path}"
        
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": upload_file.content_type or "image/jpeg"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, content=file_content, headers=headers)
            if response.status_code == 200:
                response = {"success": True, "url": f"{settings.SUPABASE_URL}/storage/v1/object/public/bolisetti-files/{file_path}"}
            else:
                response = {"success": False, "error": f"Upload failed: {response.text}"}
        
        if response and response.get("success"):
            # Create media record in database
            media_data = {
                "title": f"Project Image - {upload_file.filename or 'image'}",
                "mediaUrl": response.get("url"),
                "type": "IMAGE",
                "uniqueCode": unique_code,
                "entityType": "PROJECT",
                "entityId": project_id
            }
            
            # Create media record in database
            from app.database import db_client
            async with db_client:
                media_result = await db_client.create_media(media_data)
            
            if media_result and media_result.get("success"):
                return {
                    "success": True,
                    "mediaId": media_result.get("data", {}).get("id"),
                    "mediaUrl": response.get("url"),
                    "uniqueCode": unique_code
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to create media record"
                }
        else:
            return {
                "success": False,
                "error": "Failed to upload file to storage"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Upload failed: {str(e)}"
        }

async def get_project_images(project_id: str, user_token: Optional[str] = None) -> Dict[str, Any]:
    """Get all images for a specific project"""
    try:
        from app.database import db_client
        async with db_client:
            result = await db_client.get_media_by_entity("PROJECT", project_id)
        return result
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to fetch project images: {str(e)}"
        }

async def delete_project_image(media_id: str, user_token: Optional[str] = None) -> bool:
    """Delete project image from storage and media table"""
    try:
        from app.database import db_client
        async with db_client:
            # First get media record to get file URL
            media_record = await db_client.get_media(media_id)
            if not media_record:
                return False
                
            file_url = media_record.get("mediaUrl")
            
            if file_url:
                # Delete from Supabase Storage
                await delete_file_from_supabase(file_url)
            
            # Delete from media table
            delete_result = await db_client.delete_media(media_id)
            return delete_result
        
    except Exception as e:
        return False

async def delete_file_from_supabase(file_url: str) -> bool:
    """Delete file from Supabase Storage directly"""
    try:
        # Extract file path from URL
        if "bolisetti-files/" in file_url:
            file_path = file_url.split("bolisetti-files/")[1]
        else:
            file_path = file_url.split("/")[-1]
        
        # Delete from Supabase Storage
        url = f"{settings.SUPABASE_URL}/storage/v1/object/bolisetti-files/{file_path}"
        headers = {
            "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(url, headers=headers)
            return response.status_code == 200
    except Exception as e:
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
