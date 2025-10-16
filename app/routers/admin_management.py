from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import Optional, List
from app.models import (
    User, UserCreate, UserUpdate, Role, RoleCreate, 
    Grievance, GrievanceUpdate, News, NewsUpdate,
    Project, ProjectCreate, ProjectUpdate, Admin
)
from app.auth import get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/admin", tags=["admin-management"])

# User Management
@router.get("/users", response_model=List[User])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all users (Admin only)"""
    try:
        result = await zenstack_client.get_users(skip=skip, take=limit)
        if result and 'data' in result:
            return result['data']
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/users/{user_id}", response_model=User)
async def get_user_by_id(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Get user by ID (Admin only)"""
    try:
        result = await zenstack_client.get_user(user_id)
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update user (Admin only)"""
    try:
        update_data = {k: v for k, v in user_data.dict().items() if v is not None}
        result = await zenstack_client.update_user(user_id, update_data)
        
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete user (Admin only)"""
    try:
        result = await zenstack_client.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )

# Grievance Management
@router.get("/grievances", response_model=List[Grievance])
async def get_all_grievances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all grievances (Admin only)"""
    try:
        result = await zenstack_client.get_grievances(skip=skip, take=limit)
        if result and 'data' in result:
            grievances = result['data']
            if status_filter:
                grievances = [g for g in grievances if g.get('status') == status_filter]
            return grievances
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievances: {str(e)}"
        )

@router.put("/grievances/{grievance_id}", response_model=Grievance)
async def update_grievance(
    grievance_id: str,
    grievance_data: GrievanceUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update grievance (Admin only)"""
    try:
        update_data = {k: v for k, v in grievance_data.dict().items() if v is not None}
        result = await zenstack_client.update_grievance(grievance_id, update_data)
        
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update grievance: {str(e)}"
        )

# News Management
@router.post("/news", response_model=News)
async def create_news(
    news_data: NewsUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create news (Admin only)"""
    try:
        result = await zenstack_client.create_news(news_data.dict())
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create news"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create news: {str(e)}"
        )

@router.put("/news/{news_id}", response_model=News)
async def update_news(
    news_id: str,
    news_data: NewsUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update news (Admin only)"""
    try:
        update_data = {k: v for k, v in news_data.dict().items() if v is not None}
        result = await zenstack_client.update_news(news_id, update_data)
        
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="News not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update news: {str(e)}"
        )

@router.delete("/news/{news_id}")
async def delete_news(
    news_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete news (Admin only)"""
    try:
        result = await zenstack_client.delete_news(news_id)
        return {"message": "News deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete news: {str(e)}"
        )

# Project Management
@router.post("/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create project (Admin only)"""
    try:
        result = await zenstack_client.create_project(project_data.dict())
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )

@router.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update project (Admin only)"""
    try:
        update_data = {k: v for k, v in project_data.dict().items() if v is not None}
        result = await zenstack_client.update_project(project_id, update_data)
        
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete project (Admin only)"""
    try:
        result = await zenstack_client.delete_project(project_id)
        return {"message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

# Dashboard Statistics
@router.get("/dashboard/stats")
async def get_dashboard_stats(current_admin: dict = Depends(get_current_admin)):
    """Get dashboard statistics (Admin only)"""
    try:
        # Get counts for various entities
        users_result = await zenstack_client.get_users()
        grievances_result = await zenstack_client.get_grievances()
        news_result = await zenstack_client.get_news()
        projects_result = await zenstack_client.get_projects()
        
        stats = {
            "total_users": len(users_result.get('data', [])) if users_result else 0,
            "total_grievances": len(grievances_result.get('data', [])) if grievances_result else 0,
            "total_news": len(news_result.get('data', [])) if news_result else 0,
            "total_projects": len(projects_result.get('data', [])) if projects_result else 0,
        }
        
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )
