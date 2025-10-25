from fastapi import APIRouter, HTTPException
from app.database import db_client
from typing import List

router = APIRouter(prefix="/departments")

@router.get("/")
async def get_departments():
    """Get all grievance departments from the database"""
    try:
        async with db_client:
            departments = await db_client.get_grievance_departments()
            return departments
    except Exception as e:
        print(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

@router.get("/{department_id}")
async def get_department(department_id: str):
    """Get a specific department by ID"""
    try:
        async with db_client:
            department = await db_client.get_grievance_department_by_id(department_id)
            if not department:
                raise HTTPException(status_code=404, detail="Department not found")
            return department
    except Exception as e:
        print(f"Error fetching department: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch department")
