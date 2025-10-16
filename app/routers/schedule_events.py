from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from datetime import datetime, date
from app.models import ScheduleEvent, ScheduleEventCreate, ScheduleEventUpdate
from app.auth import get_current_user, get_current_admin
from app.zenstack_client import zenstack_client

router = APIRouter(prefix="/schedule_events", tags=["schedule_events"])

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
        print(f"Fetching schedule events with skip={skip}, limit={limit}")
        result = await zenstack_client.get_schedule_events(
            skip=skip,
            take=limit,
            user_token=current_admin.get('token')
        )
        print(f"ZenStack response: {result}")
        events = result.get('data', [])
        
        # Apply date filters if provided
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
            events = [e for e in events if e.get('eventDatetime') >= start_datetime.isoformat()]
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            events = [e for e in events if e.get('eventDatetime') <= end_datetime.isoformat()]
        
        return events
    except Exception as e:
        print(f"Error in get_schedule_events: {str(e)}")
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
        result = await zenstack_client.get_schedule_event(
            event_id=event_id,
            user_token=current_admin.get('token')
        )
        # Extract the actual event data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled event not found"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch scheduled event: {str(e)}"
        )

@router.post("/", response_model=ScheduleEvent)
async def create_schedule_event(
    event_data: ScheduleEventCreate,
    current_admin: dict = Depends(get_current_admin)
):
    """Create a new scheduled event (Admin only)"""
    try:
        result = await zenstack_client.create_schedule_event(
            event_data=event_data.dict(),
            user_token=current_admin.get('token')
        )
        # Extract the actual event data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create scheduled event: {str(e)}"
        )

@router.put("/{event_id}", response_model=ScheduleEvent)
async def update_schedule_event(
    event_id: str,
    event_update: ScheduleEventUpdate,
    current_admin: dict = Depends(get_current_admin)
):
    """Update a scheduled event (Admin only)"""
    try:
        # Check if event exists first
        existing_event = await zenstack_client.get_schedule_event(
            event_id=event_id,
            user_token=current_admin.get('token')
        )
        if not existing_event or not existing_event.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled event not found"
            )
        
        update_data = {k: v for k, v in event_update.dict().items() if v is not None}
        if not update_data:
            return existing_event.get('data', existing_event)
        
        result = await zenstack_client.update_schedule_event(
            event_id=event_id,
            event_data=update_data,
            user_token=current_admin.get('token')
        )
        # Extract the actual event data from the ZenStack response
        if 'data' in result:
            return result['data']
        else:
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update scheduled event: {str(e)}"
        )

@router.delete("/{event_id}")
async def delete_schedule_event(
    event_id: str,
    current_admin: dict = Depends(get_current_admin)
):
    """Delete a scheduled event (Admin only)"""
    try:
        # Check if event exists first
        existing_event = await zenstack_client.get_schedule_event(
            event_id=event_id,
            user_token=current_admin.get('token')
        )
        if not existing_event or not existing_event.get('data'):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Scheduled event not found"
            )
        
        await zenstack_client.delete_schedule_event(
            event_id=event_id,
            user_token=current_admin.get('token')
        )
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
        
        result = await zenstack_client.get_schedule_events(
            user_token=current_admin.get('token')
        )
        events = result.get('data', [])
        
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
