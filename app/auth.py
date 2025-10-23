from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.models import TokenData
from app.zenstack_client import zenstack_client
from app.otp_service import otp_service
# Removed direct Prisma imports - using ZenStack client instead

# Password hashing for admin authentication
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token scheme
security = HTTPBearer()

# Password functions removed - using OTP authentication instead

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.algorithm)
    return encoded_jwt

async def get_user_by_email(email: str) -> Optional[dict]:
    """Get user by email from database via ZenStack"""
    try:
        from app.zenstack_client import zenstack_client
        user = await zenstack_client.get_user_by_email(email)
        
        # Extract actual user data from ZenStack response
        if user and 'data' in user:
            actual_user = user['data']
            return actual_user
        return user
    except Exception:
        return None

# Old email/password authentication removed - using OTP authentication instead

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current authenticated user"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.algorithm])
        user_id: str = payload.get("userId")
        phone_number: str = payload.get("phoneNumber")
        
        if user_id is None:
            raise credentials_exception
            
        # Get user by phone number (more reliable than by ID)
        user = await zenstack_client.get_user_by_phone(phone_number, credentials.credentials)
        
        if user is None:
            raise credentials_exception
            
        # Return user data with token for ZenStack
        user['token'] = credentials.credentials  # Add token for ZenStack requests
        return user
        
    except JWTError as e:
        raise credentials_exception

async def get_current_active_user(current_user: dict = Depends(get_current_user)) -> dict:
    """Get current active user"""
    if not current_user.get("isActive", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

# New authentication functions for voter ID + phone system
async def validate_voter_id(voter_id: str) -> bool:
    """Validate if voter ID exists in the database"""
    try:
        voter_record = await zenstack_client.get_voter_id(voter_id)
        return voter_record is not None and voter_record.get('data', {}).get('isActive', False)
    except Exception:
        return False

async def create_user_session(user_id: str, phone_number: str) -> dict:
    """Create a new user session with 7-day expiration"""
    try:
        expires_at = datetime.utcnow() + timedelta(days=7)
        session_data = {
            "userId": user_id,
            "phoneNumber": phone_number,
            "expiresAt": expires_at.isoformat() + "Z",
            "isActive": True
        }
        
        result = await zenstack_client.create_session(session_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

async def get_user_by_phone(phone_number: str) -> Optional[dict]:
    """Get user by phone number"""
    try:
        # Get all users and filter by phone number
        all_users = await zenstack_client.get_users()
        if all_users and 'data' in all_users:
            users = all_users['data']
            for user in users:
                if user.get('phoneNumber') == phone_number:
                    return user
        return None
    except Exception:
        return None

async def create_user_from_phone(phone_number: str, voter_id: str) -> dict:
    """Create a new user with phone number and voter ID"""
    try:
        user_data = {
            "phoneNumber": phone_number,
            "voterId": voter_id,
            "isActive": True
            # firstName, lastName, email are optional - not included in creation
            # User can add them later through profile section
        }
        
        result = await zenstack_client.create_user(user_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )

async def get_current_user_by_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current user by JWT token (new system)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.algorithm])
        user_id: str = payload.get("userId")
        phone_number: str = payload.get("phoneNumber")
        
        if user_id is None or phone_number is None:
            raise credentials_exception
            
        # Check if user has active session
        session = await zenstack_client.get_user_session(user_id)
        if not session or not session.get('data'):
            raise credentials_exception
            
        # Get user details
        user = await zenstack_client.get_user(user_id)
        if not user or not user.get('data'):
            raise credentials_exception
            
        return user['data']
        
    except JWTError:
        raise credentials_exception

async def authenticate_phone_user(phone_number: str, voter_id: str) -> dict:
    """Authenticate user with phone number and voter ID"""
    # Only validate voter ID if it's provided (not empty)
    if voter_id and not await validate_voter_id(voter_id):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid voter ID"
        )
    
    # Check if user exists
    user = await get_user_by_phone(phone_number)
    
    if not user:
        # Create new user
        user_result = await create_user_from_phone(phone_number, voter_id)
        user = user_result.get('data', user_result)
    
    # Create session
    session = await create_user_session(user['id'], phone_number)
    
    return user

# Separate Admin Authentication System
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

async def get_admin_by_email(email: str) -> Optional[dict]:
    """Get admin by email from Admin table"""
    try:
        # Get all admins and filter by email
        all_admins = await zenstack_client.get_admins()
        if all_admins and 'data' in all_admins:
            admins = all_admins['data']
            for admin in admins:
                if admin.get('email') == email and admin.get('isActive', True):
                    return admin
        return None
    except Exception:
        return None

async def authenticate_admin(email: str, password: str) -> dict:
    """Authenticate admin with email and password from Admin table"""
    admin = await get_admin_by_email(email)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Verify password
    if not verify_password(password, admin.get('password', '')):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Update last login
    await zenstack_client.update_admin(admin['id'], {'lastLogin': datetime.utcnow().isoformat() + 'Z'})
    
    return admin

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current admin from Admin table"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.algorithm])
        admin_id: str = payload.get("adminId")
        user_type: str = payload.get("userType", "user")
        
        if admin_id is None or user_type != "admin":
            raise credentials_exception
            
        # Get all admins and filter by ID (same pattern as user auth)
        all_admins = await zenstack_client.get_admins()
        
        if all_admins and 'data' in all_admins:
            admins = all_admins['data']
            for admin in admins:
                if admin.get('id') == admin_id and admin.get('isActive', True):
                    return admin
        
        raise credentials_exception
        
    except JWTError:
        raise credentials_exception
    except Exception:
        raise credentials_exception
