from fastapi import APIRouter, HTTPException
from app.zenstack_client import zenstack_client
from typing import List

router = APIRouter(prefix="/constituencies", tags=["constituencies"])

@router.get("/")
async def get_constituencies():
    """Get all constituencies from the database"""
    try:
        # Fetch all constituencies from the database
        constituencies = await zenstack_client.get_constituencies()
        return constituencies
    except Exception as e:
        print(f"Error fetching constituencies: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch constituencies")

@router.get("/{constituency_id}")
async def get_constituency(constituency_id: str):
    """Get a specific constituency by ID"""
    try:
        constituency = await zenstack_client.get_constituency_by_id(constituency_id)
        if not constituency:
            raise HTTPException(status_code=404, detail="Constituency not found")
        return constituency
    except Exception as e:
        print(f"Error fetching constituency: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch constituency")
