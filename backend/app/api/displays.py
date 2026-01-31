"""
Display API router - CRUD operations and power control for displays.

Endpoints:
- GET /api/v1/displays - List all displays
- POST /api/v1/displays - Create new display
- GET /api/v1/displays/{id} - Get display by ID
- PUT /api/v1/displays/{id} - Update display
- DELETE /api/v1/displays/{id} - Delete display
- POST /api/v1/displays/{id}/power - Control display power
- GET /api/v1/displays/{id}/status - Get display power status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.db.models import Display
from app.schemas.display import (
    DisplayCreate,
    DisplayUpdate,
    DisplayResponse,
    PowerRequest,
    PowerStatusResponse,
)
from app.adapters.bravia import BraviaAdapter

router = APIRouter(prefix="/displays", tags=["displays"])


def get_bravia_adapter():
    """Dependency injection for BraviaAdapter."""
    return BraviaAdapter()


@router.get("", response_model=List[DisplayResponse])
async def list_displays(db: Session = Depends(get_db)):
    """List all displays."""
    displays = db.query(Display).all()
    return displays


@router.post("", response_model=DisplayResponse, status_code=status.HTTP_201_CREATED)
async def create_display(
    display_data: DisplayCreate, db: Session = Depends(get_db)
):
    """Create a new display."""
    # Check for duplicate IP address
    existing = db.query(Display).filter(Display.ip_address == display_data.ip_address).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Display with IP address {display_data.ip_address} already exists",
        )
    
    # Create new display
    display = Display(
        name=display_data.name,
        ip_address=display_data.ip_address,
        psk=display_data.psk,
        location=display_data.location,
        tags=display_data.tags or {},
        status="unknown",
    )
    
    try:
        db.add(display)
        db.commit()
        db.refresh(display)
        return display
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )


@router.get("/{display_id}", response_model=DisplayResponse)
async def get_display(display_id: int, db: Session = Depends(get_db)):
    """Get display by ID."""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Display with ID {display_id} not found",
        )
    return display


@router.put("/{display_id}", response_model=DisplayResponse)
async def update_display(
    display_id: int, display_data: DisplayUpdate, db: Session = Depends(get_db)
):
    """Update display by ID."""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Display with ID {display_id} not found",
        )
    
    # Update only provided fields
    update_data = display_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(display, field, value)
    
    try:
        db.commit()
        db.refresh(display)
        return display
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Database integrity error: {str(e)}",
        )


@router.delete("/{display_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_display(display_id: int, db: Session = Depends(get_db)):
    """Delete display by ID."""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Display with ID {display_id} not found",
        )
    
    db.delete(display)
    db.commit()
    return None


@router.post("/{display_id}/power")
async def control_power(
    display_id: int, 
    power_request: PowerRequest, 
    db: Session = Depends(get_db),
    bravia: BraviaAdapter = Depends(get_bravia_adapter)
):
    """Control display power (on/off)."""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Display with ID {display_id} not found",
        )
    
    success = await bravia.set_power(
        display.ip_address, display.psk, power_request.on
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to power {'on' if power_request.on else 'off'} display {display_id}",
        )
    
    display.status = "active" if power_request.on else "standby"
    display.last_seen = datetime.utcnow()
    db.commit()
    
    return {
        "success": True,
        "message": f"Display {display_id} powered {'on' if power_request.on else 'off'} successfully",
        "display_id": display_id,
    }


@router.get("/{display_id}/status", response_model=PowerStatusResponse)
async def get_power_status(
    display_id: int, 
    db: Session = Depends(get_db),
    bravia: BraviaAdapter = Depends(get_bravia_adapter)
):
    """Get display power status."""
    display = db.query(Display).filter(Display.id == display_id).first()
    if not display:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Display with ID {display_id} not found",
        )
    
    power_status = await bravia.get_power_status(display.ip_address, display.psk)
    
    display.status = power_status
    display.last_seen = datetime.utcnow()
    db.commit()
    
    return PowerStatusResponse(
        display_id=display_id,
        status=power_status,
        last_checked=datetime.utcnow(),
    )
