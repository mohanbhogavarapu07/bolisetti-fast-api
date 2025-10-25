"""
Role-based access control decorators for API endpoints
"""
from functools import wraps
from fastapi import HTTPException, status, Depends
from typing import Callable, Any
from app.auth import get_current_user, get_current_admin


def admin_required(func: Callable) -> Callable:
    """
    Decorator to require admin access for an endpoint
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if current_admin is in kwargs
        if 'current_admin' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin authentication required"
            )
        return await func(*args, **kwargs)
    return wrapper


def user_or_admin_required(func: Callable) -> Callable:
    """
    Decorator to allow either user or admin access
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Check if either current_user or current_admin is in kwargs
        if 'current_user' not in kwargs and 'current_admin' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        return await func(*args, **kwargs)
    return wrapper


def owner_or_admin_required(func: Callable) -> Callable:
    """
    Decorator to allow access if user owns the resource or is admin
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This will be implemented in the specific endpoint logic
        return await func(*args, **kwargs)
    return wrapper


def get_auth_dependency(require_admin: bool = False):
    """
    Get the appropriate authentication dependency based on requirements
    """
    if require_admin:
        return Depends(get_current_admin)
    else:
        return Depends(get_current_user)


def check_resource_ownership(resource_user_id: str, current_user: dict, current_admin: dict = None) -> bool:
    """
    Check if current user owns the resource or is admin
    """
    # Admin can access any resource
    if current_admin:
        return True
    
    # User can only access their own resources
    if current_user and current_user.get("id") == resource_user_id:
        return True
    
    return False


def check_admin_or_owner(resource_user_id: str, current_user: dict = None, current_admin: dict = None) -> bool:
    """
    Check if current user is admin or owns the resource
    """
    # Admin can access any resource
    if current_admin:
        return True
    
    # User can only access their own resources
    if current_user and current_user.get("id") == resource_user_id:
        return True
    
    return False
