from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from app.models import (
    Admin, AdminToken, AdminLoginRequest, AdminCreate, AdminUpdate
)
from app.auth import (
    create_access_token, get_current_admin, authenticate_admin
)
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/admin/auth", tags=["admin-authentication"])
security = HTTPBearer()

@router.post("/login", response_model=AdminToken)
async def admin_login(request: AdminLoginRequest):
    """
    Admin login with email and password
    """
    try:
        # Authenticate admin
        admin = await authenticate_admin(request.email, request.password)
        
        # Create JWT token with admin-specific data
        access_token_expires = timedelta(hours=8)  # Admin tokens expire in 8 hours
        access_token = create_access_token(
            data={
                "adminId": admin["id"], 
                "email": request.email,
                "userType": "admin"
            }, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": 8 * 60 * 60,  # 8 hours in seconds
            "user_type": "admin"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin login failed: {str(e)}"
        )

@router.get("/me", response_model=Admin)
async def get_current_admin_info(current_admin: dict = Depends(get_current_admin)):
    """Get current admin information"""
    return current_admin

@router.post("/logout")
async def admin_logout(current_admin: dict = Depends(get_current_admin)):
    """Admin logout"""
    try:
        # For JWT tokens, logout is handled client-side by removing the token
        # You could implement token blacklisting here if needed
        return {"message": "Admin logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Admin logout failed: {str(e)}"
        )

@router.get("/validate")
async def validate_admin_access(current_admin: dict = Depends(get_current_admin)):
    """Validate admin access and return admin info"""
    return {
        "message": "Admin access validated",
        "admin": {
            "id": current_admin.get("id"),
            "email": current_admin.get("email"),
            "firstName": current_admin.get("firstName"),
            "lastName": current_admin.get("lastName"),
            "isActive": current_admin.get("isActive"),
            "lastLogin": current_admin.get("lastLogin")
        }
    }

# Admin Management Routes
@router.post("/create", response_model=Admin)
async def create_admin(
    admin_data: AdminCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create new admin (Super admin only)"""
    try:
        from app.auth import get_password_hash
        from app.zenstack_client import zenstack_client
        
        # Hash password
        hashed_password = get_password_hash(admin_data.password)
        
        # Create admin data
        create_data = {
            "firstName": admin_data.firstName,
            "lastName": admin_data.lastName,
            "email": admin_data.email,
            "password": hashed_password,
            "isActive": admin_data.isActive
        }
        
        result = await zenstack_client.create_admin(create_data)
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create admin"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create admin: {str(e)}"
        )

@router.get("/list", response_model=list[Admin])
async def list_admins(current_admin: dict = Depends(get_current_admin)):
    """List all admins (Admin only)"""
    try:
        from app.zenstack_client import zenstack_client
        
        result = await zenstack_client.get_admins()
        if result and 'data' in result:
            return result['data']
        return []
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch admins: {str(e)}"
        )

@router.put("/update/{admin_id}", response_model=Admin)
async def update_admin(
    admin_id: str,
    admin_data: AdminUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update admin (Admin only)"""
    try:
        from app.auth import get_password_hash
        from app.zenstack_client import zenstack_client
        
        update_data = {k: v for k, v in admin_data.dict().items() if v is not None}
        
        # Hash password if provided
        if 'password' in update_data:
            update_data['password'] = get_password_hash(update_data['password'])
        
        result = await zenstack_client.update_admin(admin_id, update_data)
        if result and 'data' in result:
            return result['data']
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update admin: {str(e)}"
        )

@router.delete("/delete/{admin_id}")
async def delete_admin(
    admin_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete admin (Super admin only)"""
    try:
        from app.zenstack_client import zenstack_client
        
        # Prevent self-deletion
        if admin_id == current_admin.get('id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account"
            )
        
        result = await zenstack_client.delete_admin(admin_id)
        return {"message": "Admin deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete admin: {str(e)}"
        )
