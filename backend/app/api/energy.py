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
POWER_ON_WATTS = 100.0
POWER_STANDBY_WATTS = 0.5
COST_PER_KWH = 0.12
CO2_PER_KWH = 0.4


class DisplaySavings(BaseModel):
    display_id: int
    display_name: str
    total_hours_off: float
    energy_saved_kwh: float
    cost_saved_eur: float
    co2_reduced_kg: float


class EnergySavingsResponse(BaseModel):
    total_hours_off: float
    energy_saved_kwh: float
    cost_saved_eur: float
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
        cost_saved_eur = energy_saved_kwh * COST_PER_KWH
        co2_reduced_kg = energy_saved_kwh * CO2_PER_KWH
        
        # Get display name
        display = db.query(Display).filter(Display.id == disp_id).first()
        display_name = display.name if display else f"Display {disp_id}"
        
        display_savings_map[disp_id] = DisplaySavings(
            display_id=disp_id,
            display_name=display_name,
            total_hours_off=round(hours_off, 2),
            energy_saved_kwh=round(energy_saved_kwh, 2),
            cost_saved_eur=round(cost_saved_eur, 2),
            co2_reduced_kg=round(co2_reduced_kg, 2)
        )
    
    # Calculate totals
    total_hours_off = sum(d.total_hours_off for d in display_savings_map.values())
    total_energy_kwh = sum(d.energy_saved_kwh for d in display_savings_map.values())
    total_cost_eur = sum(d.cost_saved_eur for d in display_savings_map.values())
    total_co2_kg = sum(d.co2_reduced_kg for d in display_savings_map.values())
    
    return EnergySavingsResponse(
        total_hours_off=round(total_hours_off, 2),
        energy_saved_kwh=round(total_energy_kwh, 2),
        cost_saved_eur=round(total_cost_eur, 2),
        co2_reduced_kg=round(total_co2_kg, 2),
        start_date=start_date,
        end_date=end_date,
        displays=list(display_savings_map.values())
    )


class DailyEnergyData(BaseModel):
    date: str
    value: float


class EnergyHistoryResponse(BaseModel):
    metric: str
    days: int
    data: List[DailyEnergyData]


@router.get("/history", response_model=EnergyHistoryResponse)
async def get_energy_history(
    days: int = Query(30, description="Number of days to retrieve (default 30)"),
    metric: str = Query("energy", description="Metric type: energy, cost, time, co2"),
    db: Session = Depends(get_db)
):
    """
    Get historical energy data aggregated by day for chart visualization.
    
    Query Parameters:
    - days: Number of days to retrieve (default 30)
    - metric: Type of metric - "energy" (kWh), "cost" (EUR), "time" (hours), "co2" (kg)
    
    Returns:
    - Array of daily aggregated values for the specified metric
    """
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    power_logs = db.query(PowerLog).filter(
        PowerLog.timestamp >= start_date,
        PowerLog.timestamp <= end_date
    ).order_by(PowerLog.timestamp).all()
    
    from collections import defaultdict
    logs_by_display = defaultdict(list)
    for log in power_logs:
        logs_by_display[log.display_id].append(log)
    
    daily_data = defaultdict(float)
    
    for disp_id, logs in logs_by_display.items():
        last_off_time = None
        
        for log in logs:
            if log.action == "off":
                last_off_time = log.timestamp
            elif log.action == "on" and last_off_time:
                current_time = last_off_time
                end_time = log.timestamp
                
                while current_time < end_time:
                    day_key = current_time.date().isoformat()
                    day_end = datetime.combine(current_time.date(), datetime.max.time())
                    segment_end = min(end_time, day_end)
                    hours_in_day = (segment_end - current_time).total_seconds() / 3600
                    
                    daily_data[day_key] += hours_in_day
                    current_time = datetime.combine(current_time.date() + timedelta(days=1), datetime.min.time())
                
                last_off_time = None
        
        if last_off_time:
            current_time = last_off_time
            end_time = end_date
            
            while current_time < end_time:
                day_key = current_time.date().isoformat()
                day_end = datetime.combine(current_time.date(), datetime.max.time())
                segment_end = min(end_time, day_end)
                hours_in_day = (segment_end - current_time).total_seconds() / 3600
                
                daily_data[day_key] += hours_in_day
                current_time = datetime.combine(current_time.date() + timedelta(days=1), datetime.min.time())
    
    result_data = []
    current_date = start_date.date()
    
    while current_date <= end_date.date():
        day_key = current_date.isoformat()
        hours_off = daily_data.get(day_key, 0.0)
        
        if metric == "energy":
            power_saved_watts = POWER_ON_WATTS - POWER_STANDBY_WATTS
            value = (hours_off * power_saved_watts) / 1000
        elif metric == "cost":
            power_saved_watts = POWER_ON_WATTS - POWER_STANDBY_WATTS
            energy_kwh = (hours_off * power_saved_watts) / 1000
            value = energy_kwh * COST_PER_KWH
        elif metric == "time":
            value = hours_off
        elif metric == "co2":
            power_saved_watts = POWER_ON_WATTS - POWER_STANDBY_WATTS
            energy_kwh = (hours_off * power_saved_watts) / 1000
            value = energy_kwh * CO2_PER_KWH
        else:
            value = 0.0
        
        result_data.append(DailyEnergyData(date=day_key, value=round(value, 2)))
        current_date += timedelta(days=1)
    
    return EnergyHistoryResponse(
        metric=metric,
        days=days,
        data=result_data
    )
