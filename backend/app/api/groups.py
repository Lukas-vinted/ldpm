"""
Group API router - CRUD operations and bulk power control for groups.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import asyncio

from app.db.database import get_db
from app.db.models import Group, Display, DisplayGroup
from app.schemas.group import (
    GroupCreate, GroupUpdate, GroupResponse,
    AddDisplaysRequest, RemoveDisplaysRequest,
    BulkPowerRequest, BulkPowerResponse
)
from app.adapters.bravia import BraviaAdapter

router = APIRouter(prefix="/groups", tags=["groups"])


def get_bravia_adapter():
    """Dependency injection for BraviaAdapter."""
    return BraviaAdapter()


@router.get("", response_model=List[GroupResponse])
async def list_groups(db: Session = Depends(get_db)):
    """List all groups."""
    groups = db.query(Group).all()
    result = []
    for group in groups:
        display_count = db.query(DisplayGroup).filter(DisplayGroup.group_id == group.id).count()
        group_data = GroupResponse.model_validate(group)
        group_data.display_count = display_count
        result.append(group_data)
    return result


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(group_data: GroupCreate, db: Session = Depends(get_db)):
    """Create a new group."""
    existing = db.query(Group).filter(Group.name == group_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group with name '{group_data.name}' already exists"
        )
    
    group = Group(name=group_data.name, description=group_data.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    
    result = GroupResponse.model_validate(group)
    result.display_count = 0
    return result


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: int, db: Session = Depends(get_db)):
    """Get group by ID."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    display_count = db.query(DisplayGroup).filter(DisplayGroup.group_id == group_id).count()
    result = GroupResponse.model_validate(group)
    result.display_count = display_count
    return result


@router.put("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: int, group_data: GroupUpdate, db: Session = Depends(get_db)):
    """Update group by ID."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    update_data = group_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(group, field, value)
    
    db.commit()
    db.refresh(group)
    
    display_count = db.query(DisplayGroup).filter(DisplayGroup.group_id == group_id).count()
    result = GroupResponse.model_validate(group)
    result.display_count = display_count
    return result


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Delete group by ID."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    db.delete(group)
    db.commit()
    return None


@router.post("/{group_id}/displays", response_model=GroupResponse)
async def add_displays(group_id: int, request: AddDisplaysRequest, db: Session = Depends(get_db)):
    """Add displays to group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    for display_id in request.display_ids:
        display = db.query(Display).filter(Display.id == display_id).first()
        if not display:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Display with ID {display_id} not found"
            )
        
        existing = db.query(DisplayGroup).filter(
            DisplayGroup.group_id == group_id,
            DisplayGroup.display_id == display_id
        ).first()
        
        if not existing:
            db.add(DisplayGroup(group_id=group_id, display_id=display_id))
    
    db.commit()
    
    display_count = db.query(DisplayGroup).filter(DisplayGroup.group_id == group_id).count()
    result = GroupResponse.model_validate(group)
    result.display_count = display_count
    return result


@router.delete("/{group_id}/displays")
async def remove_displays(group_id: int, request: RemoveDisplaysRequest, db: Session = Depends(get_db)):
    """Remove displays from group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    for display_id in request.display_ids:
        db.query(DisplayGroup).filter(
            DisplayGroup.group_id == group_id,
            DisplayGroup.display_id == display_id
        ).delete()
    
    db.commit()
    return {"message": f"Removed {len(request.display_ids)} displays from group"}


@router.post("/{group_id}/power", response_model=BulkPowerResponse)
async def bulk_power_control(
    group_id: int,
    request: BulkPowerRequest,
    db: Session = Depends(get_db),
    bravia: BraviaAdapter = Depends(get_bravia_adapter)
):
    """Control power for all displays in group."""
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group with ID {group_id} not found"
        )
    
    display_groups = db.query(DisplayGroup).filter(DisplayGroup.group_id == group_id).all()
    display_ids = [dg.display_id for dg in display_groups]
    displays = db.query(Display).filter(Display.id.in_(display_ids)).all()
    
    async def control_display(display: Display):
        success = await bravia.set_power(display.ip_address, display.psk, request.on)
        return {"display_id": display.id, "success": success}
    
    results = await asyncio.gather(*[control_display(d) for d in displays])
    
    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful
    
    return BulkPowerResponse(
        group_id=group_id,
        total_displays=len(displays),
        successful=successful,
        failed=failed,
        results=results
    )
