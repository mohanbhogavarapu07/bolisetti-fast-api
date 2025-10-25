from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.models import TokenData
from app.database import db_client
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
    """Get user by email from database"""
    try:
        async with db_client:
            user = await db_client.get_user_by_email(email)
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
        async with db_client:
            user = await db_client.get_user_by_phone(phone_number)
        
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
        print(f"[DEBUG] Validating voter ID: {voter_id}")
        async with db_client:
            voter_record = await db_client.get_voter_id(voter_id)
        print(f"[DEBUG] Voter record found: {voter_record is not None}")
        if voter_record:
            print(f"[DEBUG] Voter record details: {voter_record}")
            is_active = voter_record.get('isActive', False)
            print(f"[DEBUG] Voter is active: {is_active}")
            return is_active
        else:
            print(f"[DEBUG] No voter record found for: {voter_id}")
            return False
    except Exception as e:
        print(f"[DEBUG] Exception in validate_voter_id: {str(e)}")
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
        
        async with db_client:
            result = await db_client.create_session(session_data)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create session: {str(e)}"
        )

async def get_user_by_phone(phone_number: str) -> Optional[dict]:
    """Get user by phone number"""
    try:
        # Get user by phone number
        async with db_client:
            user = await db_client.get_user_by_phone(phone_number)
        return user
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
        
        async with db_client:
            result = await db_client.create_user(user_data)
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
        async with db_client:
            session = await db_client.get_user_session(user_id)
            if not session:
                raise credentials_exception
                
            # Get user details
            user = await db_client.get_user(user_id)
            if not user:
                raise credentials_exception
            
        return user
        
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
        async with db_client:
            admin = await db_client.get_admin_by_email(email)
            return admin
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
    
    stored_password = admin.get('password', '')
    
    # Direct password comparison (no hashing)
    password_valid = (password == stored_password)
    
    if not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials"
        )
    
    # Update last login
    async with db_client:
        await db_client.update_admin(admin['id'], {'lastLogin': datetime.utcnow().isoformat() + 'Z'})
    
    return admin

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """Get current admin from Admin table"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"[DEBUG] Validating admin token: {credentials.credentials[:20]}...")
        
        # Decode JWT token
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.algorithm])
        admin_id: str = payload.get("adminId")
        user_type: str = payload.get("userType", "user")
        
        print(f"[DEBUG] Token payload - adminId: {admin_id}, userType: {user_type}")
        
        if admin_id is None or user_type != "admin":
            print(f"[DEBUG] Token validation failed - adminId: {admin_id}, userType: {user_type}")
            raise credentials_exception
            
        # Get admin by ID
        async with db_client:
            admin = await db_client.get_admin_by_id(admin_id)
        
        print(f"[DEBUG] Admin found: {admin is not None}")
        if admin:
            print(f"[DEBUG] Admin active: {admin.get('isActive', True)}")
        
        if not admin or not admin.get('isActive', True):
            print(f"[DEBUG] Admin not found or inactive")
            raise credentials_exception
        return admin
        
    except JWTError as e:
        print(f"[DEBUG] JWT Error: {str(e)}")
        raise credentials_exception
    except Exception as e:
        print(f"[DEBUG] Exception: {str(e)}")
        raise credentials_exception
