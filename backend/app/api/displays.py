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

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from datetime import datetime
import csv
import io

from app.db.database import get_db
from app.db.models import Display
from app.schemas.display import (
    DisplayCreate,
    DisplayUpdate,
    DisplayResponse,
    PowerRequest,
    PowerStatusResponse,
    CSVImportResponse,
    CSVImportRowError,
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


@router.post("/import", response_model=CSVImportResponse)
async def import_displays_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Import displays from CSV file.
    
    CSV format: ip_address,name,location
    - If IP exists: update the display's name and location
    - If IP doesn't exist: create new display with status="unknown"
    """
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file",
        )
    
    created_count = 0
    updated_count = 0
    failed_count = 0
    failed_rows: List[CSVImportRowError] = []
    total_processed = 0
    
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(decoded))
        
        expected_columns = {'ip_address', 'name', 'location'}
        if csv_reader.fieldnames:
            actual_columns = set(csv_reader.fieldnames)
            if not expected_columns.issubset(actual_columns):
                missing = expected_columns - actual_columns
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"CSV missing required columns: {', '.join(missing)}. Expected: ip_address,name,location",
                )
        
        for row_num, row in enumerate(csv_reader, start=2):
            total_processed += 1
            
            ip_address = row.get('ip_address', '').strip()
            name = row.get('name', '').strip()
            location = row.get('location', '').strip()
            
            if not ip_address:
                failed_count += 1
                failed_rows.append(CSVImportRowError(
                    row_number=row_num,
                    data=row,
                    error="IP address is required"
                ))
                continue
            
            if not name:
                failed_count += 1
                failed_rows.append(CSVImportRowError(
                    row_number=row_num,
                    data=row,
                    error="Display name is required"
                ))
                continue
            
            existing = db.query(Display).filter(Display.ip_address == ip_address).first()
            
            if existing:
                existing.name = name
                if location:
                    existing.location = location
                updated_count += 1
            else:
                new_display = Display(
                    name=name,
                    ip_address=ip_address,
                    psk=None,
                    location=location if location else None,
                    tags={},
                    status="unknown",
                )
                db.add(new_display)
                created_count += 1
        
        db.commit()
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Please ensure the CSV is UTF-8 encoded.",
        )
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV parsing error: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}",
        )
    
    return CSVImportResponse(
        created_count=created_count,
        updated_count=updated_count,
        failed_count=failed_count,
        total_processed=total_processed,
        failed_rows=failed_rows,
    )
