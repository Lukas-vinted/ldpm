"""
Energy Savings API router - Calculate energy savings from power logs.

Endpoints:
- GET /api/v1/energy/savings - Calculate energy savings for date range
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import Optional, List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import PowerLog, Display
from pydantic import BaseModel

router = APIRouter(prefix="/energy", tags=["energy"])


# Constants for Sony BRAVIA power consumption
POWER_ON_WATTS = 100.0  # Typical power consumption when TV is ON
POWER_STANDBY_WATTS = 0.5  # Typical power consumption in standby mode
COST_PER_KWH = 0.12  # Cost per kilowatt-hour in USD
CO2_PER_KWH = 0.4  # kg CO2 per kWh


class DisplaySavings(BaseModel):
    """Energy savings for a single display."""
    display_id: int
    display_name: str
    total_hours_off: float
    energy_saved_kwh: float
    cost_saved_usd: float
    co2_reduced_kg: float


class EnergySavingsResponse(BaseModel):
    """Response model for energy savings calculation."""
    total_hours_off: float
    energy_saved_kwh: float
    cost_saved_usd: float
    co2_reduced_kg: float
    start_date: Optional[str]
    end_date: Optional[str]
    displays: List[DisplaySavings]


@router.get("/savings", response_model=EnergySavingsResponse)
async def calculate_energy_savings(
    start_date: Optional[str] = Query(None, description="Start date in ISO format (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date in ISO format (YYYY-MM-DD)"),
    display_id: Optional[int] = Query(None, description="Filter by specific display ID"),
    db: Session = Depends(get_db)
):
    """
    Calculate energy savings from PowerLog data.
    
    Algorithm:
    1. Query PowerLog for power state changes in date range
    2. Calculate total hours TV was OFF (between "off" and "on" events)
    3. Calculate energy saved: hours_off * (100W - 0.5W) = hours_off * 99.5W
    4. Convert to kWh: energy_kWh = energy_W * hours / 1000
    5. Calculate cost saved: energy_kWh * $0.12
    6. Calculate CO2 reduced: energy_kWh * 0.4 kg
    
    Query Parameters:
    - start_date: Start date (optional, ISO format)
    - end_date: End date (optional, ISO format)
    - display_id: Filter by specific display (optional)
    
    Returns:
    - Total energy savings across all displays or specific display
    """
    # Parse date range
    try:
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
    except ValueError as e:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format. Use ISO format (YYYY-MM-DD): {str(e)}"
        )
    
    # Build query filters
    query = db.query(PowerLog).order_by(PowerLog.timestamp)
    
    if start_dt:
        query = query.filter(PowerLog.timestamp >= start_dt)
    if end_dt:
        query = query.filter(PowerLog.timestamp <= end_dt)
    if display_id:
        query = query.filter(PowerLog.display_id == display_id)
    
    # Get all power logs in date range
    power_logs = query.all()
    
    # Calculate savings per display
    display_savings_map = {}
    
    # Group logs by display
    from collections import defaultdict
    logs_by_display = defaultdict(list)
    for log in power_logs:
        logs_by_display[log.display_id].append(log)
    
    # Calculate hours off for each display
    for disp_id, logs in logs_by_display.items():
        hours_off = 0.0
        last_off_time = None
        
        for log in logs:
            if log.action == "off":
                # Mark the start of an "off" period
                last_off_time = log.timestamp
            elif log.action == "on" and last_off_time:
                # Calculate duration of "off" period
                duration = (log.timestamp - last_off_time).total_seconds() / 3600
                hours_off += duration
                last_off_time = None
        
        # If display is still off at end of period, count until now or end_date
        if last_off_time:
            end_time = end_dt if end_dt else datetime.utcnow()
            duration = (end_time - last_off_time).total_seconds() / 3600
            hours_off += duration
        
        # Calculate energy savings
        power_saved_watts = POWER_ON_WATTS - POWER_STANDBY_WATTS  # 99.5W
        energy_saved_wh = hours_off * power_saved_watts
        energy_saved_kwh = energy_saved_wh / 1000
        cost_saved_usd = energy_saved_kwh * COST_PER_KWH
        co2_reduced_kg = energy_saved_kwh * CO2_PER_KWH
        
        # Get display name
        display = db.query(Display).filter(Display.id == disp_id).first()
        display_name = display.name if display else f"Display {disp_id}"
        
        display_savings_map[disp_id] = DisplaySavings(
            display_id=disp_id,
            display_name=display_name,
            total_hours_off=round(hours_off, 2),
            energy_saved_kwh=round(energy_saved_kwh, 2),
            cost_saved_usd=round(cost_saved_usd, 2),
            co2_reduced_kg=round(co2_reduced_kg, 2)
        )
    
    # Calculate totals
    total_hours_off = sum(d.total_hours_off for d in display_savings_map.values())
    total_energy_kwh = sum(d.energy_saved_kwh for d in display_savings_map.values())
    total_cost_usd = sum(d.cost_saved_usd for d in display_savings_map.values())
    total_co2_kg = sum(d.co2_reduced_kg for d in display_savings_map.values())
    
    return EnergySavingsResponse(
        total_hours_off=round(total_hours_off, 2),
        energy_saved_kwh=round(total_energy_kwh, 2),
        cost_saved_usd=round(total_cost_usd, 2),
        co2_reduced_kg=round(total_co2_kg, 2),
        start_date=start_date,
        end_date=end_date,
        displays=list(display_savings_map.values())
    )
