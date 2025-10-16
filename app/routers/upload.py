from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List
from app.auth import get_current_user
from app.utils import save_upload_file, validate_file_size, validate_file_type, ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES, ALLOWED_DOCUMENT_TYPES
from app.models import MediaType
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload an image file"""
    # Validate file size
    if not validate_file_size(file):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large"
        )
    
    # Validate file type
    if not validate_file_type(file, ALLOWED_IMAGE_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only images are allowed."
        )
    
    try:
        url = await save_upload_file(file, "images", current_user.get('token'))
        
        # Create media record
        media_data = {
            "title": file.filename or "Uploaded Image",
            "mediaUrl": url,
            "type": MediaType.IMAGE
        }
        
        media_result = await zenstack_client.create_media(
            media_data=media_data,
            user_token=current_user.get('token')
        )
        
        # Extract media ID from result
        media_id = None
        if isinstance(media_result, dict) and 'data' in media_result:
            media_id = media_result['data'].get('id')
        elif isinstance(media_result, dict) and 'id' in media_result:
            media_id = media_result['id']
        
        return {
            "url": url, 
            "filename": file.filename,
            "mediaId": media_id,
            "media": media_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )

@router.post("/video")
async def upload_video(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a video file"""
    # Validate file size
    if not validate_file_size(file):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large"
        )
    
    # Validate file type
    if not validate_file_type(file, ALLOWED_VIDEO_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only videos are allowed."
        )
    
    try:
        url = await save_upload_file(file, "videos", current_user.get('token'))
        return {"url": url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload video: {str(e)}"
        )

@router.post("/document")
async def upload_document(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a document file"""
    # Validate file size
    if not validate_file_size(file):
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size too large"
        )
    
    # Validate file type
    if not validate_file_type(file, ALLOWED_DOCUMENT_TYPES):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Only documents are allowed."
        )
    
    try:
        url = await save_upload_file(file, "documents", current_user.get('token'))
        return {"url": url, "filename": file.filename}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

@router.post("/multiple")
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload multiple files"""
    if len(files) > 10:  # Limit to 10 files
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many files. Maximum 10 files allowed."
        )
    
    uploaded_files = []
    errors = []
    
    for file in files:
        try:
            # Validate file size
            if not validate_file_size(file):
                errors.append(f"{file.filename}: File size too large")
                continue
            
            # Determine file type and upload accordingly
            if validate_file_type(file, ALLOWED_IMAGE_TYPES):
                url = await save_upload_file(file, "images", current_user.get('token'))
            elif validate_file_type(file, ALLOWED_VIDEO_TYPES):
                url = await save_upload_file(file, "videos", current_user.get('token'))
            elif validate_file_type(file, ALLOWED_DOCUMENT_TYPES):
                url = await save_upload_file(file, "documents", current_user.get('token'))
            else:
                errors.append(f"{file.filename}: Invalid file type")
                continue
            
            uploaded_files.append({
                "filename": file.filename,
                "url": url,
                "content_type": file.content_type
            })
        except Exception as e:
            errors.append(f"{file.filename}: {str(e)}")
    
    return {
        "uploaded_files": uploaded_files,
        "errors": errors,
        "total_uploaded": len(uploaded_files),
        "total_errors": len(errors)
    }
