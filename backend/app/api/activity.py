"""
Activity log API router - provides power state change history.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import PowerLog, Display
from pydantic import BaseModel


class ActivityLogResponse(BaseModel):
    """Response model for activity log entry."""
    id: int
    display_id: int
    display_name: str
    action: str
    timestamp: datetime
    source: str
    
    class Config:
        from_attributes = True


router = APIRouter(prefix="/activity", tags=["activity"])


@router.get("", response_model=List[ActivityLogResponse])
async def get_activity_logs(
    limit: int = Query(default=100, le=500, description="Maximum number of logs to return"),
    offset: int = Query(default=0, ge=0, description="Number of logs to skip"),
    display_id: Optional[int] = Query(default=None, description="Filter by display ID"),
    action: Optional[str] = Query(default=None, description="Filter by action (on/off)"),
    hours: Optional[int] = Query(default=None, description="Only show logs from last N hours"),
    db: Session = Depends(get_db)
):
    """
    Get activity logs (power state changes) for displays.
    
    Returns logs in reverse chronological order (newest first).
    
    Query Parameters:
    - limit: Maximum number of logs to return (default: 100, max: 500)
    - offset: Number of logs to skip for pagination (default: 0)
    - display_id: Filter logs for specific display
    - action: Filter by action type ("on" or "off")
    - hours: Only show logs from last N hours (e.g., hours=24 for last 24 hours)
    """
    query = db.query(PowerLog, Display).join(Display, PowerLog.display_id == Display.id)
    
    # Filter by display_id
    if display_id is not None:
        query = query.filter(PowerLog.display_id == display_id)
    
    # Filter by action
    if action is not None:
        query = query.filter(PowerLog.action == action)
    
    # Filter by time range
    if hours is not None:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(PowerLog.timestamp >= cutoff_time)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(desc(PowerLog.timestamp))
    
    # Apply pagination
    query = query.limit(limit).offset(offset)
    
    # Execute query
    results = query.all()
    
    # Transform results
    logs = []
    for power_log, display in results:
        logs.append(ActivityLogResponse(
            id=power_log.id,
            display_id=power_log.display_id,
            display_name=display.name,
            action=power_log.action,
            timestamp=power_log.timestamp,
            source=power_log.source
        ))
    
    return logs
