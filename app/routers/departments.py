from fastapi import APIRouter, HTTPException
from app.zenstack_client import zenstack_client
from typing import List

router = APIRouter(prefix="/departments", tags=["departments"])

@router.get("/")
async def get_departments():
    """Get all grievance departments from the database"""
    try:
        # Fetch all departments from the database
        departments = await zenstack_client.get_grievance_departments()
        return departments
    except Exception as e:
        print(f"Error fetching departments: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch departments")

@router.get("/{department_id}")
async def get_department(department_id: str):
    """Get a specific department by ID"""
    try:
        department = await zenstack_client.get_grievance_department_by_id(department_id)
        if not department:
            raise HTTPException(status_code=404, detail="Department not found")
        return department
    except Exception as e:
        print(f"Error fetching department: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch department")
