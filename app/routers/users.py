from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models import User, UserUpdate
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get all users with pagination"""
    try:
        result = await zenstack_client.get_users(
            skip=skip, 
            take=limit, 
            user_token=current_user.get('token')
        )
        return result.get('data', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID"""
    try:
        result = await zenstack_client.get_user(
            user_id=user_id,
            user_token=current_user.get('token')
        )
        # Extract the actual user data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user information"""
    try:
        # Check if user exists first
        existing_user_result = await zenstack_client.get_user(
            user_id=user_id,
            user_token=current_user.get('token')
        )
        
        if 'data' not in existing_user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        existing_user = existing_user_result['data']
        
        # Only allow users to update their own profile or admin users
        if existing_user["id"] != current_user["id"]:
            # Add admin check here if needed
            pass
        
        # Update user via ZenStack
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        if not update_data:
            return existing_user
        
        result = await zenstack_client.update_user(
            user_id=user_id,
            user_data=update_data,
            user_token=current_user.get('token')
        )
        
        # Extract the updated user data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete user (soft delete by setting isActive to False)"""
    try:
        # Check if user exists first
        existing_user_result = await zenstack_client.get_user(
            user_id=user_id,
            user_token=current_user.get('token')
        )
        
        if 'data' not in existing_user_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        existing_user = existing_user_result['data']
        
        # Only allow users to delete their own account or admin users
        if existing_user["id"] != current_user["id"]:
            # Add admin check here if needed
            pass
        
        # Soft delete user via ZenStack
        result = await zenstack_client.update_user(
            user_id=user_id,
            user_data={"isActive": False},
            user_token=current_user.get('token')
        )
        
        return {"message": "User deactivated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate user: {str(e)}"
        )

@router.get("/by-email/{email}", response_model=User)
async def get_user_by_email(
    email: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user by email (for debugging)"""
    try:
        result = await zenstack_client.get_user_by_email(
            email=email,
            user_token=current_user.get('token')
        )
        if result and 'data' in result:
            return result['data']
        elif result:
            return result
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch user: {str(e)}"
        )

@router.get("/me/profile", response_model=User)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    """Get current user's profile"""
    return current_user

@router.put("/me/profile", response_model=User)
async def update_my_profile(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user's profile"""
    try:
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        if not update_data:
            return current_user
        
        # Update user via ZenStack
        result = await zenstack_client.update_user(
            user_id=current_user["id"],
            user_data=update_data,
            user_token=current_user.get('token')
        )
        
        # Extract the updated user data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

# Admin-only endpoints
@router.get("/admin/all", response_model=List[User])
async def get_all_users_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all users (Admin only)"""
    try:
        result = await zenstack_client.get_users(
            skip=skip, 
            take=limit, 
            user_token=current_admin.get('token')
        )
        return result.get('data', [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )
