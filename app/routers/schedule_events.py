from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from app.models import ScheduleEvent, ScheduleEventCreate, ScheduleEventUpdate
from app.auth import get_current_user, get_current_admin
from app.database import db_client
from app.decorators import admin_required

router = APIRouter(prefix="/schedule_events")

@router.get("/", response_model=List[ScheduleEvent])
async def get_schedule_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Get all scheduled events with optional date filters"""
    try:
        async with db_client:
            events = await db_client.get_schedule_events(skip=skip, take=limit)
        
        # Apply date filters if provided
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            events = [e for e in events if e.get('eventDatetime') >= start_datetime.isoformat()]
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            events = [e for e in events if e.get('eventDatetime') <= end_datetime.isoformat()]
        
        return events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch schedule events: {str(e)}"
        )

@router.get("/{event_id}", response_model=ScheduleEvent)
async def get_schedule_event_by_id(
    event_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get scheduled event by ID"""
    try:
        async with db_client:
            event = await db_client.get_schedule_event(event_id)
            if not event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scheduled event not found"
                )
            return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scheduled event: {str(e)}"
        )

@router.post("/", response_model=ScheduleEvent)
@admin_required
async def create_schedule_event(
    event_data: ScheduleEventCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new scheduled event (Admin only)"""
    try:
        # Convert datetime to ISO string format for JSON serialization
        event_dict = event_data.dict()
        if 'eventDatetime' in event_dict and event_dict['eventDatetime']:
            event_dict['eventDatetime'] = event_dict['eventDatetime'].isoformat()
        
        async with db_client:
            event = await db_client.create_schedule_event(event_dict)
            return event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled event: {str(e)}"
        )

@router.put("/{event_id}", response_model=ScheduleEvent)
@admin_required
async def update_schedule_event(
    event_id: str,
    event_update: ScheduleEventUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a scheduled event (Admin only)"""
    try:
        async with db_client:
            # Check if event exists first
            existing_event = await db_client.get_schedule_event(event_id)
            if not existing_event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scheduled event not found"
                )
            
            update_data = {k: v for k, v in event_update.dict().items() if v is not None}
            if not update_data:
                return existing_event
            
            # Convert datetime to ISO string format for JSON serialization
            if 'eventDatetime' in update_data and update_data['eventDatetime']:
                update_data['eventDatetime'] = update_data['eventDatetime'].isoformat()
            
            event = await db_client.update_schedule_event(event_id, update_data)
            return event
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduled event: {str(e)}"
        )

@router.delete("/{event_id}")
@admin_required
async def delete_schedule_event(
    event_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a scheduled event (Admin only)"""
    try:
        async with db_client:
            # Check if event exists first
            existing_event = await db_client.get_schedule_event(event_id)
            if not existing_event:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Scheduled event not found"
                )
            
            await db_client.delete_schedule_event(event_id)
        return {"message": "Scheduled event deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete scheduled event: {str(e)}"
        )

@router.get("/upcoming/events", response_model=List[ScheduleEvent])
async def get_upcoming_events(
    days: int = Query(7, ge=1, le=30),
    current_user: dict = Depends(get_current_user)
):
    """Get upcoming events for the next N days"""
    try:
        from datetime import timedelta
        start_date = datetime.now()
        end_date = start_date + timedelta(days=days)
        
        async with db_client:
            events = await db_client.get_schedule_events()
        
        # Filter events within the date range
        filtered_events = []
        for event in events:
            event_datetime = event.get('eventDatetime')
            if event_datetime:
                event_date = datetime.fromisoformat(event_datetime.replace('Z', '+00:00'))
                if start_date <= event_date <= end_date:
                    filtered_events.append(event)
        
        # Sort by event datetime
        filtered_events.sort(key=lambda x: x.get('eventDatetime', ''))
        
        return filtered_events
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch upcoming events: {str(e)}"
        )
