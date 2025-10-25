from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from app.models import News, NewsCreate, NewsUpdate
from app.auth import get_current_user, get_current_admin
from app.database import db_client
from app.utils import save_upload_file

router = APIRouter(prefix="/news")

@router.get("/", response_model=List[News])
async def get_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all news articles"""
    try:
        async with db_client:
            news = await db_client.get_news(skip=skip, take=limit)
            return news
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )

@router.get("/{news_id}", response_model=News)
async def get_news_by_id(
    news_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get news article by ID"""
    try:
        async with db_client:
            news = await db_client.get_news_by_id(news_id)
            if not news:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="News article not found"
                )
            return news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )

@router.post("/", response_model=News)
async def create_news(
    title: str = Form(...),
    content: str = Form(...),
    file: Optional[UploadFile] = File(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new news article with optional image upload (Admin only)"""
    try:
        # Handle image upload if provided
        image_url = None
        if file and file.filename:
            try:
                # Upload to Supabase storage
                image_url = await save_upload_file(file, "news")
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to upload image: {str(e)}"
                )
        
        # Create news data
        news_data = {
            "title": title,
            "content": content,
            "imageUrl": image_url
        }
        
        async with db_client:
            news = await db_client.create_news(news_data)
            return news
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create news: {str(e)}"
        )
@router.put("/{news_id}", response_model=News)
async def update_news(
    news_id: str,
    news_update: NewsUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a news article (Admin only)"""
    try:
        async with db_client:
            # Check if news exists first
            existing_news = await db_client.get_news_by_id(news_id)
            if not existing_news:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="News article not found"
                )
            
            update_data = {k: v for k, v in news_update.dict().items() if v is not None}
            if not update_data:
                return existing_news
            
            news = await db_client.update_news(news_id, update_data)
            return news
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update news: {str(e)}"
        )

@router.delete("/{news_id}")
async def delete_news(
    news_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a news article (Admin only)"""
    try:
        async with db_client:
            # Check if news exists first
            existing_news = await db_client.get_news_by_id(news_id)
            if not existing_news:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="News article not found"
                )
            
            await db_client.delete_news(news_id)
            return {"message": "News article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete news: {str(e)}"
        )

