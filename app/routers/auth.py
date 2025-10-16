from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer
from app.models import (
    User, Token, PhoneLoginRequest, OTPVerificationRequest, 
    UserProfileUpdate, VoterId, OTP, Session
)
from app.auth import (
    create_access_token, get_current_user_by_token, authenticate_phone_user,
    validate_voter_id, create_user_session
)
from app.otp_service import otp_service
from app.zenstack_client import zenstack_client
from datetime import timedelta
from app.config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])
security = HTTPBearer()

@router.post("/send-otp")
async def send_otp(request: PhoneLoginRequest):
    """
    Send OTP to phone number after validating voter ID
    """
    try:
        # Check if user exists with phone number
        existing_user = await zenstack_client.get_user_by_phone(request.phoneNumber)
        
        if existing_user:
            # User exists - check if voter ID matches
            if existing_user.get('voterId') != request.voterId:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Voter ID not linked to this phone number"
                )
            print(f"Existing user validated: {existing_user.get('id')}")
        else:
            # New user path: voterId must exist and be active in VoterId table
            if not await validate_voter_id(request.voterId):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid voter ID"
                )
            print(f"New user - voter ID validated: {request.voterId}")
        
        # Send OTP
        result = await otp_service.send_otp(request.phoneNumber)
        
        if result["success"]:
            return {
                "message": "OTP sent successfully",
                "expires_in": result["expires_in"]
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

@router.post("/verify-otp", response_model=Token)
async def verify_otp(request: OTPVerificationRequest):
    """
    Verify OTP and create user session
    """
    try:
        # Verify OTP
        otp_result = await otp_service.verify_otp(request.phoneNumber, request.otp)
        
        if not otp_result["success"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=otp_result["message"]
            )
        
        # Authenticate user (create or get user)
        user = await authenticate_phone_user(request.phoneNumber, request.voterId)
        
        # Create JWT token with 7-day expiration
        access_token_expires = timedelta(days=7)
        access_token = create_access_token(
            data={"userId": user["id"], "phoneNumber": request.phoneNumber}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token, 
            "token_type": "bearer",
            "expires_in": 7 * 24 * 60 * 60  # 7 days in seconds
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify OTP: {str(e)}"
        )

@router.get("/me", response_model=User)
async def get_current_user_info(current_user: dict = Depends(get_current_user_by_token)):
    """Get current user information"""
    return current_user

@router.put("/profile", response_model=User)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user_by_token)
):
    """Update user profile"""
    try:
        # Update user profile
        update_data = {k: v for k, v in profile_data.dict().items() if v is not None}
        
        result = await zenstack_client.update_user(current_user["id"], update_data)
        
        if 'data' in result:
            return result['data']
        else:
            return result
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user_by_token)):
    """Logout user and invalidate session"""
    try:
        # Invalidate all active sessions for this user
        await zenstack_client.invalidate_sessions_by_user(current_user["id"])
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )

@router.get("/validate-voter-id/{voter_id}")
async def validate_voter_id_endpoint(voter_id: str):
    """Validate if voter ID exists in the system"""
    try:
        is_valid = await validate_voter_id(voter_id)
        return {
            "voter_id": voter_id,
            "is_valid": is_valid
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate voter ID: {str(e)}"
        )

# Admin endpoints for voter ID management
@router.post("/admin/load-voter-ids")
async def load_voter_ids():
    """Load voter IDs from file (Admin only)"""
    try:
        # This would typically be protected by admin authentication
        # For now, we'll just return a message
        return {
            "message": "Use the load_voter_ids.py script to load voter IDs",
            "script": "python load_voter_ids.py"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load voter IDs: {str(e)}"
        )
