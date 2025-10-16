from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.auth import get_current_user
from app.models import Media, MediaCreate, MediaUpdate
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/media", tags=["media"])

@router.get("/", response_model=List[Media])
async def get_media(
    skip: int = 0,
    take: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Get all media"""
    try:
        result = await zenstack_client.get_media(
            skip=skip,
            take=take,
            user_token=current_user.get('token')
        )
        # Extract the actual media data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result if isinstance(result, list) else []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch media: {str(e)}"
        )

@router.get("/{media_id}", response_model=Media)
async def get_media_by_id(
    media_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get media by ID"""
    try:
        result = await zenstack_client.get_media_item(
            media_id=media_id,
            user_token=current_user.get('token')
        )
        # Extract the actual media data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch media: {str(e)}"
        )

@router.post("/", response_model=Media)
async def create_media(
    media_data: MediaCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new media"""
    try:
        result = await zenstack_client.create_media(
            media_data=media_data.dict(),
            user_token=current_user.get('token')
        )
        # Extract the actual media data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create media: {str(e)}"
        )

@router.put("/{media_id}", response_model=Media)
async def update_media(
    media_id: str,
    media_update: MediaUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update media"""
    try:
        result = await zenstack_client.update_media(
            media_id=media_id,
            media_data=media_update.dict(),
            user_token=current_user.get('token')
        )
        # Extract the actual media data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update media: {str(e)}"
        )

@router.delete("/{media_id}")
async def delete_media(
    media_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete media"""
    try:
        result = await zenstack_client.delete_media(
            media_id=media_id,
            user_token=current_user.get('token')
        )
        return {"success": True, "message": "Media deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete media: {str(e)}"
        )