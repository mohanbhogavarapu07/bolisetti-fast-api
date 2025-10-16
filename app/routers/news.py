from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models import News, NewsCreate, NewsUpdate
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/news", tags=["news"])

@router.get("/", response_model=List[News])
async def get_news(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all news articles"""
    try:
        result = await zenstack_client.get_news(
            skip=skip,
            take=limit,
            user_token=current_admin.get('token')
        )
        return result.get('data', [])
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
        result = await zenstack_client.get_news_item(
            news_id=news_id,
            user_token=current_admin.get('token')
        )
        # Extract the actual news data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News article not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch news: {str(e)}"
        )

@router.post("/", response_model=News)
async def create_news(
    news_data: NewsCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new news article (Admin only)"""
    try:
        result = await zenstack_client.create_news(
            news_data=news_data.dict(),
            user_token=current_admin.get('token')
        )
        # Extract the actual news data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
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
        # Check if news exists first
        existing_news = await zenstack_client.get_news_item(
            news_id=news_id,
            user_token=current_admin.get('token')
        )
        if not existing_news or not existing_news.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News article not found"
            )
        
        update_data = {k: v for k, v in news_update.dict().items() if v is not None}
        if not update_data:
            return existing_news.get('data', existing_news)
        
        result = await zenstack_client.update_news(
            news_id=news_id,
            news_data=update_data,
            user_token=current_admin.get('token')
        )
        # Extract the actual news data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
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
        # Check if news exists first
        existing_news = await zenstack_client.get_news_item(
            news_id=news_id,
            user_token=current_admin.get('token')
        )
        if not existing_news or not existing_news.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News article not found"
            )
        
        await zenstack_client.delete_news(
            news_id=news_id,
            user_token=current_admin.get('token')
        )
        return {"message": "News article deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete news: {str(e)}"
        )

