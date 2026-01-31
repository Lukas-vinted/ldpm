"""
Schedule API router - CRUD operations for power schedules.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.db.models import Schedule
from app.schemas.schedule import ScheduleCreate, ScheduleUpdate, ScheduleResponse

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=List[ScheduleResponse])
async def list_schedules(db: Session = Depends(get_db)):
    """List all schedules."""
    schedules = db.query(Schedule).all()
    return schedules


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(schedule_data: ScheduleCreate, db: Session = Depends(get_db)):
    """Create a new schedule."""
    schedule = Schedule(
        name=schedule_data.name,
        display_id=schedule_data.display_id,
        group_id=schedule_data.group_id,
        action=schedule_data.action,
        cron_expression=schedule_data.cron_expression,
        enabled=schedule_data.enabled
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


@router.get("/{schedule_id}", response_model=ScheduleResponse)
async def get_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Get schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {schedule_id} not found"
        )
    return schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
async def update_schedule(
    schedule_id: int, schedule_data: ScheduleUpdate, db: Session = Depends(get_db)
):
    """Update schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {schedule_id} not found"
        )
    
    update_data = schedule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(schedule, field, value)
    
    db.commit()
    db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Delete schedule by ID."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {schedule_id} not found"
        )
    
    db.delete(schedule)
    db.commit()
    return None


@router.post("/{schedule_id}/enable")
async def enable_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Enable schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {schedule_id} not found"
        )
    
    schedule.enabled = True
    db.commit()
    return {"message": f"Schedule {schedule_id} enabled"}


@router.post("/{schedule_id}/disable")
async def disable_schedule(schedule_id: int, db: Session = Depends(get_db)):
    """Disable schedule."""
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    if not schedule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Schedule with ID {schedule_id} not found"
        )
    
    schedule.enabled = False
    db.commit()
    return {"message": f"Schedule {schedule_id} disabled"}
