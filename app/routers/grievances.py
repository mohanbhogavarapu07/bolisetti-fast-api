from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from app.models import Grievance, GrievanceCreate, GrievanceUpdate, GrievanceStatus, Priority, GrievanceStatusUpdate
from app.auth import get_current_user, get_current_admin
from fastapi import Depends
from app.database import db_client
from app.utils import save_upload_file
from app.decorators import admin_required, check_resource_ownership

router = APIRouter(prefix="/grievances")

async def get_current_user_or_admin(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Get current user or admin - allows both to access the endpoint"""
    from app.auth import get_current_user, get_current_admin
    from fastapi import HTTPException, status
    
    # Try user authentication first
    try:
        user = await get_current_user(credentials)
        return user
    except:
        pass
    
    # Try admin authentication
    try:
        admin = await get_current_admin(credentials)
        return admin
    except:
        pass
    
    # If both fail, raise authentication error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

@router.get("/", response_model=List[Grievance])
async def get_grievances(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[GrievanceStatus] = Query(None),
    priority_filter: Optional[Priority] = Query(None),
    constituency_filter: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user_or_admin)
):
    """Get all grievances with optional filters (Users and Admins)"""
    try:
        async with db_client:
            grievances = await db_client.get_grievances(skip=skip, take=limit)
            return grievances
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
    current_user: dict = Depends(get_current_user_or_admin)
):
    """Get current user's grievances (Users and Admins)"""
    try:
        async with db_client:
            all_grievances = await db_client.get_grievances(skip=skip, take=limit)
            # Filter by current user's grievances
            user_grievances = [g for g in all_grievances if g.get('userId') == current_user["id"]]
            return user_grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user grievances: {str(e)}"
        )

@router.get("/{grievance_id}", response_model=Grievance)
async def get_grievance(
    grievance_id: str,
    current_user: dict = Depends(get_current_user_or_admin)
):
    """Get grievance by ID (Users and Admins)"""
    try:
        async with db_client:
            grievance = await db_client.get_grievance(grievance_id)
            if not grievance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Grievance not found"
                )
            return grievance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievance: {str(e)}"
        )

@router.post("/", response_model=Grievance)
async def create_grievance(
    title: str = Form(...),
    description: str = Form(...),
    address: str = Form(...),
    area: Optional[str] = Form(None),
    constituencyId: Optional[str] = Form(None),
    departmentId: Optional[str] = Form(None),
    constituency: Optional[str] = Form(None),  # Add constituency name
    department: Optional[str] = Form(None),    # Add department name
    priority: str = Form("MEDIUM"),
    file: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user_or_admin)
):
    """Create a new grievance with optional image upload (Users and Admins)"""
    try:
        # Handle image upload if provided
        image_url = None
        if file and file.filename:
            try:
                # Upload to Supabase storage
                image_url = await save_upload_file(file, "grievances")
            except Exception as e:
                # Don't fail the entire request if image upload fails
                print(f"Image upload failed: {str(e)}")
                image_url = None
        
        # Create grievance data
        # Handle both user and admin cases
        user_id = current_user.get("id")
        
        # Check if this is an admin by looking for admin-specific fields
        is_admin = (
            current_user.get("userType") == "admin" or 
            "adminId" in current_user or 
            "password" in current_user  # Admins have password field, users don't
        )
        
        if is_admin:
            # For admins, we need to use a system user ID
            try:
                async with db_client:
                    # Try to find a system user
                    system_user = await db_client.get_user_by_email("system@bolisetti.com")
                    if system_user:
                        user_id = system_user["id"]
                    else:
                        # Create a system user for admin operations
                        system_user_data = {
                            "firstName": "System",
                            "lastName": "Admin", 
                            "email": "system@bolisetti.com",
                            "phoneNumber": "0000000000",
                            "isActive": True
                        }
                        system_user = await db_client.create_user(system_user_data)
                        user_id = system_user["id"]
            except Exception as e:
                # Fallback to admin ID (this might cause foreign key error)
                user_id = current_user.get("id")
        
        # Look up constituency and department IDs if names are provided
        final_constituency_id = constituencyId
        final_department_id = departmentId
        
        if constituency and not constituencyId:
            try:
                async with db_client:
                    constituencies = await db_client.get_constituencies()
                    for const in constituencies:
                        if const.get('name', '').lower() == constituency.lower():
                            final_constituency_id = const.get('id')
                            break
            except Exception as e:
                print(f"Error looking up constituency: {str(e)}")
        
        if department and not departmentId:
            try:
                async with db_client:
                    departments = await db_client.get_grievance_departments()
                    for dept in departments:
                        if dept.get('name', '').lower() == department.lower():
                            final_department_id = dept.get('id')
                            break
            except Exception as e:
                print(f"Error looking up department: {str(e)}")
        
        grievance_data = {
            "title": title,
            "description": description,
            "address": address,
            "area": area,
            "constituencyId": final_constituency_id,
            "departmentId": final_department_id,
            "priority": priority,
            "imageUrl": image_url,
            "userId": user_id
        }
        
        async with db_client:
            grievance = await db_client.create_grievance(grievance_data)
            return grievance
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
        async with db_client:
            # Check if grievance exists first
            existing_grievance = await db_client.get_grievance(grievance_id)
            if not existing_grievance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Grievance not found"
                )
            
            # Only allow users to update their own grievances or admin users
            if existing_grievance.get("userId") != current_user["id"]:
                # Add admin check here if needed
                pass
            
            update_data = {k: v for k, v in grievance_update.dict().items() if v is not None}
            if not update_data:
                return existing_grievance
            
            grievance = await db_client.update_grievance(grievance_id, update_data)
            return grievance
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


# Admin-only endpoints
@router.get("/admin/all", response_model=List[Grievance])
@admin_required
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
        async with db_client:
            grievances = await db_client.get_grievances(skip=skip, take=limit)
            return grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch grievances: {str(e)}"
        )

@router.get("/admin/ongoing", response_model=List[Grievance])
@admin_required
async def get_ongoing_grievances_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin)
):
    """Get ongoing grievances (Admin only)"""
    try:
        async with db_client:
            all_grievances = await db_client.get_grievances(skip=skip, take=limit)
            # Filter for ongoing grievances (not completed or closed)
            ongoing_statuses = ["IN_REVIEW", "IN_PROGRESS", "ASSIGNED"]
            ongoing_grievances = [
                g for g in all_grievances 
                if g.get('status') in ongoing_statuses
            ]
            return ongoing_grievances
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch ongoing grievances: {str(e)}"
        )

@router.put("/admin/{grievance_id}/status", response_model=Grievance)
@admin_required
async def update_grievance_status_admin(
    grievance_id: str,
    status_data: GrievanceStatusUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update grievance status (Admin only)"""
    try:
        async with db_client:
            # Check if grievance exists first
            existing_grievance = await db_client.get_grievance(grievance_id)
            if not existing_grievance:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Grievance not found"
                )
            
            # Convert frontend status format to backend format
            status_mapping = {
                "Open": "OPEN",
                "In Review": "IN_REVIEW", 
                "In Progress": "IN_PROGRESS",
                "Resolved": "RESOLVED",
                "Closed": "CLOSED"
            }
            
            update_data = {}
            if status_data.status is not None:
                # Convert frontend status to backend format
                backend_status = status_mapping.get(status_data.status, status_data.status)
                update_data['status'] = backend_status
            
            if status_data.priority is not None:
                update_data['priority'] = status_data.priority
            
            if status_data.departmentId is not None:
                update_data['departmentId'] = status_data.departmentId
            
            if not update_data:
                return existing_grievance
            
            grievance = await db_client.update_grievance(grievance_id, update_data)
            return grievance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update grievance status: {str(e)}"
        )

