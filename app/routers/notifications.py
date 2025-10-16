from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from app.models import Notification, NotificationCreate, NotificationUpdate
from app.auth import get_current_user
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/user/{user_id}", response_model=List[Notification])
async def get_user_notifications(
    user_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Get notifications for a specific user"""
    try:
        result = await zenstack_client.get_notifications(
            user_id=user_id,
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        notifications = result.get('data', [])
        
        # Filter unread only if requested
        if unread_only:
            notifications = [n for n in notifications if not n.get('isRead', False)]
        
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}"
        )

@router.get("/my", response_model=List[Notification])
async def get_my_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's notifications"""
    try:
        result = await zenstack_client.get_notifications(
            user_id=current_user["id"],
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        notifications = result.get('data', [])
        
        # Filter unread only if requested
        if unread_only:
            notifications = [n for n in notifications if not n.get('isRead', False)]
        
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notifications: {str(e)}"
        )

@router.get("/public", response_model=List[Notification])
async def get_public_notifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get public notifications (notifications without userId)"""
    try:
        result = await zenstack_client.get_notifications(
            skip=skip,
            take=limit,
            user_token=current_user.get('token')
        )
        notifications = result.get('data', [])
        
        # Filter for public notifications (no userId)
        notifications = [n for n in notifications if not n.get('userId')]
        
        return notifications
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch public notifications: {str(e)}"
        )

@router.get("/{notification_id}", response_model=Notification)
async def get_notification_by_id(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get notification by ID"""
    try:
        result = await zenstack_client.get_notification(
            notification_id=notification_id,
            user_token=current_user.get('token')
        )
        notification = result.get('data', result)
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Check if user can access this notification
        if notification.get("userId") and notification["userId"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch notification: {str(e)}"
        )

@router.post("/", response_model=Notification)
async def create_notification(
    notification_data: NotificationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new notification (Admin only)"""
    # Add admin check here
    try:
        result = await zenstack_client.create_notification(
            notification_data=notification_data.dict(),
            user_token=current_user.get('token')
        )
        # Extract the actual notification data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create notification: {str(e)}"
        )

@router.put("/{notification_id}", response_model=Notification)
async def update_notification(
    notification_id: str,
    notification_update: NotificationUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a notification"""
    try:
        # Check if notification exists first
        existing_notification = await zenstack_client.get_notification(
            notification_id=notification_id,
            user_token=current_user.get('token')
        )
        if not existing_notification or not existing_notification.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notification_data = existing_notification.get('data', existing_notification)
        # Check if user can update this notification
        if notification_data.get("userId") and notification_data["userId"] != current_user["id"]:
            # Add admin check here
            pass
        
        update_data = {k: v for k, v in notification_update.dict().items() if v is not None}
        if not update_data:
            return notification_data
        
        result = await zenstack_client.update_notification(
            notification_id=notification_id,
            notification_data=update_data,
            user_token=current_user.get('token')
        )
        # Extract the actual notification data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update notification: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a notification (Admin only)"""
    # Add admin check here
    try:
        # Check if notification exists first
        existing_notification = await zenstack_client.get_notification(
            notification_id=notification_id,
            user_token=current_user.get('token')
        )
        if not existing_notification or not existing_notification.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        await zenstack_client.delete_notification(
            notification_id=notification_id,
            user_token=current_user.get('token')
        )
        return {"message": "Notification deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete notification: {str(e)}"
        )

@router.put("/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        # Check if notification exists first
        existing_notification = await zenstack_client.get_notification(
            notification_id=notification_id,
            user_token=current_user.get('token')
        )
        if not existing_notification or not existing_notification.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        notification_data = existing_notification.get('data', existing_notification)
        # Check if user can mark this notification as read
        if notification_data.get("userId") and notification_data["userId"] != current_user["id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        result = await zenstack_client.update_notification(
            notification_id=notification_id,
            notification_data={"isRead": True},
            user_token=current_user.get('token')
        )
        return {"message": "Notification marked as read"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark notification as read: {str(e)}"
        )

@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user)
):
    """Mark all user's notifications as read"""
    try:
        # Get all user notifications
        result = await zenstack_client.get_notifications(
            user_id=current_user["id"],
            user_token=current_user.get('token')
        )
        notifications = result.get('data', [])
        
        # Update each unread notification
        for notification in notifications:
            if not notification.get('isRead', False):
                await zenstack_client.update_notification(
                    notification_id=notification['id'],
                    notification_data={"isRead": True},
                    user_token=current_user.get('token')
                )
        
        return {"message": "All notifications marked as read"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark all notifications as read: {str(e)}"
        )
