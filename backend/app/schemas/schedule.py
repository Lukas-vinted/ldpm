"""
Pydantic schemas for Schedule API endpoints.

Schemas:
- ScheduleCreate: Request body for POST /api/v1/schedules
- ScheduleUpdate: Request body for PUT /api/v1/schedules/{id}
- ScheduleResponse: Response model for Schedule objects
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime
import re


class ScheduleCreate(BaseModel):
    """Schema for creating a new schedule."""
    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    display_id: Optional[int] = Field(None, description="Target display ID (mutually exclusive with group_id)")
    group_id: Optional[int] = Field(None, description="Target group ID (mutually exclusive with display_id)")
    action: Literal["on", "off"] = Field(..., description="Power action: on or off")
    cron_expression: str = Field(..., min_length=1, max_length=255, description="Cron expression")
    enabled: bool = Field(default=True, description="Whether schedule is active")

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        """Basic cron expression validation (5 fields)."""
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 fields: minute hour day month weekday")
        return v

    @field_validator("display_id", "group_id")
    @classmethod
    def validate_target(cls, v, info):
        """Ensure exactly one of display_id or group_id is set."""
        values = info.data
        display_id = values.get("display_id")
        group_id = values.get("group_id")
        
        # This validator runs per-field, so check after both are processed
        if info.field_name == "group_id":
            if display_id is None and group_id is None:
                raise ValueError("Either display_id or group_id must be set")
            if display_id is not None and group_id is not None:
                raise ValueError("Cannot set both display_id and group_id")
        
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Morning Power On",
                "group_id": 1,
                "action": "on",
                "cron_expression": "0 7 * * MON-FRI",
                "enabled": True
            }
        }


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Schedule name")
    display_id: Optional[int] = Field(None, description="Target display ID")
    group_id: Optional[int] = Field(None, description="Target group ID")
    action: Optional[Literal["on", "off"]] = Field(None, description="Power action")
    cron_expression: Optional[str] = Field(None, description="Cron expression")
    enabled: Optional[bool] = Field(None, description="Whether schedule is active")

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: Optional[str]) -> Optional[str]:
        """Basic cron expression validation (5 fields)."""
        if v is None:
            return v
        parts = v.split()
        if len(parts) != 5:
            raise ValueError("Cron expression must have 5 fields: minute hour day month weekday")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Morning Power On",
                "cron_expression": "0 8 * * MON-FRI"
            }
        }


class ScheduleResponse(BaseModel):
    """Schema for Schedule response (returned by all endpoints)."""
    id: int
    name: str
    display_id: Optional[int]
    group_id: Optional[int]
    action: str
    cron_expression: str
    enabled: bool
    created_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Morning Power On",
                "display_id": None,
                "group_id": 1,
                "action": "on",
                "cron_expression": "0 7 * * MON-FRI",
                "enabled": True,
                "created_at": "2026-01-01T08:00:00"
            }
        }
