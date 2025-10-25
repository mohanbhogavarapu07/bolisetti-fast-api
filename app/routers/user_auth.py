from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from app.models import (
    User, UserToken, PhoneLoginRequest, OTPVerificationRequest, 
    UserProfileUpdate, UserCreate
)
from fastapi import Query
from typing import List
from app.auth import (
    create_access_token, get_current_user, get_current_admin, authenticate_phone_user,
    get_user_by_phone, create_user_from_phone, validate_voter_id
)
from app.otp_service import otp_service
from app.database import db_client
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/users")
security = HTTPBearer()

@router.post("/send-otp")
async def send_otp(request: PhoneLoginRequest):
    """
    Send OTP to phone number for user authentication
    """
    try:
        # Validate voter ID if provided
        if request.voterId and not await validate_voter_id(request.voterId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid voter ID"
            )
        
        # Send OTP
        result = await otp_service.send_otp(request.phoneNumber)
        
        if result["success"]:
            return {
                "success": True,
                "message": "OTP sent successfully",
                "expires_in": result.get("expires_in", 60)
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

@router.post("/verify-otp", response_model=UserToken)
async def verify_otp(request: OTPVerificationRequest):
    """
    Verify OTP and authenticate user
    """
    try:
        # Verify OTP
        otp_result = await otp_service.verify_otp(request.phoneNumber, request.otp)
        
        if not otp_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=otp_result["message"]
            )
        
        # Validate voter ID if provided
        if request.voterId and not await validate_voter_id(request.voterId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid voter ID"
            )
        
        # Authenticate user
        user = await authenticate_phone_user(request.phoneNumber, request.voterId)
        
        # Create JWT token
        access_token_expires = timedelta(days=7)  # User tokens expire in 7 days
        access_token = create_access_token(
            data={
                "userId": user["id"],
                "phoneNumber": request.phoneNumber,
                "userType": "user"
            },
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": 7 * 24 * 60 * 60,  # 7 days in seconds
            "user_type": "user",
            "user": user
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@router.post("/logout")
async def user_logout(current_user: dict = Depends(get_current_user)):
    """User logout"""
    try:
        # For JWT tokens, logout is handled client-side by removing the token
        # You could implement token blacklisting here if needed
        return {"message": "User logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/validate")
async def validate_user_access(current_user: dict = Depends(get_current_user)):
    """Validate user access and return user info"""
    return {
        "message": "User access validated",
        "user": {
            "id": current_user.get("id"),
            "phoneNumber": current_user.get("phoneNumber"),
            "firstName": current_user.get("firstName"),
            "lastName": current_user.get("lastName"),
            "voterId": current_user.get("voterId"),
            "isActive": current_user.get("isActive")
        }
    }

@router.put("/profile", response_model=User)
async def update_user_profile(
    profile_update: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update user profile"""
    try:
        update_data = {k: v for k, v in profile_update.dict().items() if v is not None}
        if not update_data:
            return current_user
        
        async with db_client:
            updated_user = await db_client.update_user(current_user["id"], update_data)
            return updated_user
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/register", response_model=User)
async def register_user(user_data: UserCreate):
    """Register a new user (alternative to OTP flow)"""
    try:
        # Validate voter ID if provided
        if user_data.voterId and not await validate_voter_id(user_data.voterId):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid voter ID"
            )
        
        # Check if user already exists
        existing_user = await get_user_by_phone(user_data.phoneNumber)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this phone number already exists"
            )
        
        # Create user
        async with db_client:
            user = await db_client.create_user(user_data.dict())
            return user
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

# Admin-only user management endpoints
@router.get("/admin/all", response_model=List[User])
async def get_all_users_admin(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_admin: dict = Depends(get_current_admin)
):
    """Get all users (Admin only)"""
    try:
        async with db_client:
            users = await db_client.get_users(skip=skip, take=limit)
            return users
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.delete("/admin/{user_id}")
async def delete_user_admin(
    user_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete user (Admin only)"""
    try:
        async with db_client:
            # Check if user exists first
            existing_user = await db_client.get_user(user_id)
            if not existing_user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Soft delete user (set isActive to False)
            await db_client.update_user(user_id, {"isActive": False})
            return {"message": "User deactivated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )
