from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from app.models import ScheduleEvent, ScheduleEventCreate, ScheduleEventUpdate
from app.auth import get_current_user
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/schedules", tags=["schedules"])

@router.get("/", response_model=List[ScheduleEvent])
async def get_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all schedules with optional date filters"""
    try:
        # Get schedule events from ZenStack service
        result = await zenstack_client.get_schedule_events(
            skip=skip, 
            take=limit, 
            user_token=current_user.get("token")
        )
        return result.get("data", [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {str(e)}"
        )

@router.get("/my", response_model=List[ScheduleEvent])
async def get_my_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get current user's schedules"""
    try:
        # Get user's schedule events from ZenStack service
        result = await zenstack_client.get_schedule_events(
            skip=skip, 
            take=limit, 
            user_token=current_user.get("token")
        )
        return result.get("data", [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get my schedules: {str(e)}"
        )

@router.get("/{schedule_id}", response_model=ScheduleEvent)
async def get_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get schedule by ID"""
    try:
        schedule = await zenstack_client.get_schedule_event(
            schedule_id, 
            user_token=current_user.get("token")
        )
        return schedule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule not found: {str(e)}"
        )

@router.post("/", response_model=ScheduleEvent)
async def create_schedule(
    schedule_data: ScheduleEventCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new schedule"""
    try:
        schedule = await zenstack_client.create_schedule_event(
            schedule_data.dict(), 
            user_token=current_user.get("token")
        )
        return schedule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )

@router.put("/{schedule_id}", response_model=ScheduleEvent)
async def update_schedule(
    schedule_id: str,
    schedule_update: ScheduleEventUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a schedule"""
    try:
        update_data = {k: v for k, v in schedule_update.dict().items() if v is not None}
        if not update_data:
            # Return existing schedule if no updates
            return await zenstack_client.get_schedule_event(schedule_id, user_token=current_user.get("token"))
        
        updated_schedule = await zenstack_client.update_schedule_event(
            schedule_id, 
            update_data, 
            user_token=current_user.get("token")
        )
        return updated_schedule
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )

@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        await zenstack_client.delete_schedule_event(
            schedule_id, 
            user_token=current_user.get("token")
        )
        return {"message": "Schedule deleted successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {str(e)}"
        )

@router.get("/upcoming/events", response_model=List[ScheduleEvent])
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming events for the next N days"""
    try:
        # Get upcoming schedule events from ZenStack service
        result = await zenstack_client.get_schedule_events(
            skip=0, 
            take=100, 
            user_token=current_user.get("token")
        )
        return result.get("data", [])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upcoming events: {str(e)}"
        )
