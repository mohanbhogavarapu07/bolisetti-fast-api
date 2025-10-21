from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from typing import List, Optional
from app.models import Project, ProjectCreate, ProjectUpdate
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client
from app.utils import save_upload_file

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[Project])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by project status: 'Live', 'Proposed', 'Completed'"),
    # Temporarily remove authentication for testing
    # current_user: dict = Depends(get_current_user)
):
    """Get all development projects with optional status filtering"""
    try:
        result = await zenstack_client.get_projects(
            skip=skip,
            take=limit,
            status_filter=status_filter,
            user_token=None  # No authentication required for public projects
        )
        
        # Handle different response formats
        if isinstance(result, list):
            return result
        elif isinstance(result, dict) and 'data' in result:
            return result.get('data', [])
        else:
            return []
            
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
        
        # Create project first
        result = await zenstack_client.create_project(
            project_data=project_data,
            user_token=current_admin.get('token')
        )
        
        if not result or 'data' not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create project"
            )
        
        project = result['data']
        project_id = project['id']
        
        # Upload image if provided
        if file and file.content_type and file.content_type.startswith('image/'):
            try:
                image_url = await save_upload_file(
                    upload_file=file,
                    folder="projects",
                    user_token=current_admin.get('token')
                )
                
                # Update project with image URL
                await zenstack_client.update_project(
                    project_id=project_id,
                    project_data={"imageUrl": image_url},
                    user_token=current_admin.get('token')
                )
                
                # Return project with image URL
                project['imageUrl'] = image_url
                
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

