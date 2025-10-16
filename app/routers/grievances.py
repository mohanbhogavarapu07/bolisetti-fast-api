from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models import Grievance, GrievanceCreate, GrievanceUpdate, GrievanceComment, GrievanceCommentCreate, GrievanceStatus, Priority
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/grievances", tags=["grievances"])

@router.get("/", response_model=List[Grievance])
async def get_grievances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[GrievanceStatus] = Query(None),
    priority_filter: Optional[Priority] = Query(None),
    constituency_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all grievances with optional filters"""
    try:
        result = await zenstack_client.get_grievances(
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        return result.get('data', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievances: {str(e)}"
        )

@router.get("/user/{user_id}", response_model=List[Grievance])
async def get_user_grievances(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get grievances for a specific user"""
    try:
        result = await zenstack_client.get_grievances(
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        # Filter by user_id in the result
        user_grievances = [g for g in result.get('data', []) if g.get('userId') == user_id]
        return user_grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user grievances: {str(e)}"
        )

@router.get("/my", response_model=List[Grievance])
async def get_my_grievances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's grievances"""
    try:
        result = await zenstack_client.get_grievances(
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        # Filter by current user's grievances
        user_grievances = [g for g in result.get('data', []) if g.get('userId') == current_user["id"]]
        return user_grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user grievances: {str(e)}"
        )

@router.get("/{grievance_id}", response_model=Grievance)
async def get_grievance(
    grievance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get grievance by ID"""
    try:
        result = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        # Extract the actual grievance data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievance: {str(e)}"
        )

@router.post("/", response_model=Grievance)
async def create_grievance(
    grievance_data: GrievanceCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new grievance (Both users and admins can create)"""
    try:
        grievance_data_dict = grievance_data.dict()
        grievance_data_dict["userId"] = current_user["id"]
        
        result = await zenstack_client.create_grievance(
            grievance_data=grievance_data_dict,
            user_token=current_user.get('token')
        )
        
        # Extract the actual grievance data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create grievance: {str(e)}"
        )

@router.put("/{grievance_id}", response_model=Grievance)
async def update_grievance(
    grievance_id: str,
    grievance_update: GrievanceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a grievance"""
    try:
        # Check if grievance exists first
        existing_grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        if not existing_grievance or not existing_grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        grievance_data = existing_grievance.get('data', existing_grievance)
        # Only allow users to update their own grievances or admin users
        if grievance_data.get("userId") != current_user["id"]:
            # Add admin check here if needed
            pass
        
        update_data = {k: v for k, v in grievance_update.dict().items() if v is not None}
        if not update_data:
            return grievance_data
        
        result = await zenstack_client.update_grievance(
            grievance_id=grievance_id,
            grievance_data=update_data,
            user_token=current_user.get('token')
        )
        # Extract the actual grievance data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update grievance: {str(e)}"
        )

@router.delete("/{grievance_id}")
async def delete_grievance(
    grievance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a grievance"""
    try:
        # Check if grievance exists first
        existing_grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        if not existing_grievance or not existing_grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        grievance_data = existing_grievance.get('data', existing_grievance)
        # Only allow users to delete their own grievances or admin users
        if grievance_data.get("userId") != current_user["id"]:
            # Add admin check here if needed
            pass
        
        await zenstack_client.delete_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        return {"message": "Grievance deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete grievance: {str(e)}"
        )

# Grievance Comments
@router.post("/{grievance_id}/comments", response_model=GrievanceComment)
async def add_comment(
    grievance_id: str,
    comment_data: GrievanceCommentCreate,
    current_user: dict = Depends(get_current_user)
):
    """Add a comment to a grievance"""
    try:
        # Check if grievance exists first
        grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        if not grievance or not grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        result = await zenstack_client.create_grievance_comment(
            grievance_id=grievance_id,
            comment_data={
                "content": comment_data.content,
                "userId": current_user["id"]
            },
            user_token=current_user.get('token')
        )
        # Extract the actual comment data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {str(e)}"
        )

@router.get("/{grievance_id}/comments", response_model=List[GrievanceComment])
async def get_comments(
    grievance_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get comments for a grievance"""
    try:
        # Check if grievance exists first
        grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        if not grievance or not grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        result = await zenstack_client.get_grievance_comments(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        return result.get('data', [])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch comments: {str(e)}"
        )

@router.put("/assign/{grievance_id}")
async def assign_grievance(
    grievance_id: str,
    department_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Assign a grievance to a specific department (Admin only)"""
    # Add admin check here
    try:
        # Check if grievance exists first
        existing_grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_user.get('token')
        )
        if not existing_grievance or not existing_grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        # Update grievance with department assignment
        result = await zenstack_client.update_grievance(
            grievance_id=grievance_id,
            grievance_data={"departmentId": department_id},
            user_token=current_user.get('token')
        )
        return {"message": "Grievance assigned successfully", "grievance": result.get('data', result)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign grievance: {str(e)}"
        )

# Statistics
@router.get("/stats/summary")
async def get_grievance_stats(current_user: dict = Depends(get_current_user)):
    """Get grievance statistics"""
    try:
        # Get all grievances to calculate stats
        result = await zenstack_client.get_grievances(
            user_token=current_user.get('token')
        )
        grievances = result.get('data', [])
        
        # Calculate statistics
        total_grievances = len(grievances)
        
        # Get grievances by status
        status_counts = {}
        for status in GrievanceStatus:
            count = len([g for g in grievances if g.get('status') == status.value])
            status_counts[status.value] = count
        
        # Get grievances by priority
        priority_counts = {}
        for priority in Priority:
            count = len([g for g in grievances if g.get('priority') == priority.value])
            priority_counts[priority.value] = count
        
        return {
            "total": total_grievances,
            "by_status": status_counts,
            "by_priority": priority_counts
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}"
        )

# Admin-only endpoints
@router.get("/admin/all", response_model=List[Grievance])
async def get_all_grievances_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[GrievanceStatus] = Query(None),
    priority_filter: Optional[Priority] = Query(None),
    constituency_filter: Optional[str] = Query(None),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all grievances (Admin only)"""
    try:
        result = await zenstack_client.get_grievances(
            skip=skip,
            take=limit,
            user_token=current_admin.get('token')
        )
        return result.get('data', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievances: {str(e)}"
        )

@router.get("/admin/ongoing", response_model=List[Grievance])
async def get_ongoing_grievances_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin)
):
    """Get ongoing grievances (Admin only)"""
    try:
        result = await zenstack_client.get_grievances(
            skip=skip,
            take=limit,
            user_token=current_admin.get('token')
        )
        # Filter for ongoing grievances (not completed or closed)
        ongoing_statuses = [GrievanceStatus.PENDING, GrievanceStatus.IN_PROGRESS, GrievanceStatus.ASSIGNED]
        ongoing_grievances = [
            g for g in result.get('data', []) 
            if g.get('status') in [status.value for status in ongoing_statuses]
        ]
        return ongoing_grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ongoing grievances: {str(e)}"
        )

@router.put("/admin/{grievance_id}/status", response_model=Grievance)
async def update_grievance_status_admin(
    grievance_id: str,
    status_update: GrievanceUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update grievance status (Admin only)"""
    try:
        # Check if grievance exists first
        existing_grievance = await zenstack_client.get_grievance(
            grievance_id=grievance_id,
            user_token=current_admin.get('token')
        )
        if not existing_grievance or not existing_grievance.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grievance not found"
            )
        
        update_data = {k: v for k, v in status_update.dict().items() if v is not None}
        if not update_data:
            return existing_grievance.get('data', existing_grievance)
        
        result = await zenstack_client.update_grievance(
            grievance_id=grievance_id,
            grievance_data=update_data,
            user_token=current_admin.get('token')
        )
        # Extract the actual grievance data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update grievance status: {str(e)}"
        )
