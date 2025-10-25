from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from app.models import Project, ProjectCreate, ProjectUpdate
from app.auth import get_current_user, get_current_admin
from app.database import db_client
from app.utils import save_upload_file
from app.decorators import admin_required

router = APIRouter(prefix="/projects")

@router.get("/", response_model=List[Project])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by project status: 'Live', 'Proposed', 'Completed'")
):
    """Get all development projects with optional status filtering (Public)"""
    try:
        async with db_client:
            projects = await db_client.get_projects(skip=skip, take=limit)
            return projects
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )

@router.get("/{project_id}", response_model=Project)
async def get_project_by_id(
    project_id: str
):
    """Get project by ID (Public)"""
    try:
        async with db_client:
            project = await db_client.get_project(project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}"
        )

@router.post("/", response_model=Project)
@admin_required
async def create_project(
    title: str = Form(...),
    description: str = Form(...),
    location: Optional[str] = Form(None),
    projectStatus: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Create a development project with optional image (Admin only)"""
    try:
        # Create project data
        project_data = {
            "title": title,
            "description": description,
            "location": location,
            "projectStatus": projectStatus
        }
        
        async with db_client:
            # Create project first
            project = await db_client.create_project(project_data)
            project_id = project['id']
            
            # Upload image if provided
            if file and file.content_type and file.content_type.startswith('image/'):
                try:
                    image_url = await save_upload_file(
                        upload_file=file,
                        folder="projects"
                    )
                    
                    # Update project with image URL
                    project = await db_client.update_project(project_id, {"imageUrl": image_url})
                    
                except Exception as e:
                    # Continue without image if upload fails
                    pass
            
            return project
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )
@router.put("/{project_id}", response_model=Project)
@admin_required
async def update_project(
    project_id: str,
    project_update: ProjectUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a development project (Admin only)"""
    try:
        async with db_client:
            # Check if project exists first
            existing_project = await db_client.get_project(project_id)
            if not existing_project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            
            update_data = {k: v for k, v in project_update.dict().items() if v is not None}
            if not update_data:
                return existing_project
            
            result = await db_client.update_project(project_id, update_data)
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/{project_id}")
@admin_required
async def delete_project(
    project_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a development project (Admin only)"""
    try:
        async with db_client:
            # Check if project exists first
            existing_project = await db_client.get_project(project_id)
            if not existing_project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Project not found"
                )
            
            await db_client.delete_project(project_id)
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )

