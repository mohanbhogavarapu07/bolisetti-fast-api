from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models import Project, ProjectCreate, ProjectUpdate
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[Project])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all development projects"""
    try:
        result = await zenstack_client.get_projects(
            skip=skip,
            take=limit,
            user_token=current_admin.get('token')
        )
        return result.get('data', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )

@router.get("/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get project by ID"""
    try:
        result = await zenstack_client.get_project(
            project_id=project_id,
            user_token=current_admin.get('token')
        )
        # Extract the actual project data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}"
        )

@router.post("/", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new development project (Admin only)"""
    try:
        result = await zenstack_client.create_project(
            project_data=project_data.dict(),
            user_token=current_admin.get('token')
        )
        # Extract the actual project data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )
@router.put("/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a development project (Admin only)"""
    try:
        # Check if project exists first
        existing_project = await zenstack_client.get_project(
            project_id=project_id,
            user_token=current_admin.get('token')
        )
        if not existing_project or not existing_project.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        update_data = {k: v for k, v in project_update.dict().items() if v is not None}
        if not update_data:
            return existing_project.get('data', existing_project)
        
        result = await zenstack_client.update_project(
            project_id=project_id,
            project_data=update_data,
            user_token=current_admin.get('token')
        )
        # Extract the actual project data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a development project (Admin only)"""
    try:
        # Check if project exists first
        existing_project = await zenstack_client.get_project(
            project_id=project_id,
            user_token=current_admin.get('token')
        )
        if not existing_project or not existing_project.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        await zenstack_client.delete_project(
            project_id=project_id,
            user_token=current_admin.get('token')
        )
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

