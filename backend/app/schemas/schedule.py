"""
Pydantic schemas for Schedule API endpoints.

Schemas:
- ScheduleCreate: Request body for POST /api/v1/schedules
- ScheduleUpdate: Request body for PUT /api/v1/schedules/{id}
- ScheduleResponse: Response model for Schedule objects
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Literal, List
from datetime import datetime
import re


class ScheduleCreate(BaseModel):
    """Schema for creating a new schedule."""
    name: str = Field(..., min_length=1, max_length=255, description="Schedule name")
    display_ids: List[int] = Field(default_factory=list, description="Target display IDs")
    group_ids: List[int] = Field(default_factory=list, description="Target group IDs")
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

    @model_validator(mode='after')
    def validate_target(self):
        """Ensure at least one target (display or group) is set."""
        if not self.display_ids and not self.group_ids:
            raise ValueError("At least one display_id or group_id must be set")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Morning Power On",
                "display_ids": [1, 2, 3],
                "group_ids": [1],
                "action": "on",
                "cron_expression": "0 7 * * 1-5",
                "enabled": True
            }
        }


class ScheduleUpdate(BaseModel):
    """Schema for updating an existing schedule."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Schedule name")
    display_ids: Optional[List[int]] = Field(None, description="Target display IDs")
    group_ids: Optional[List[int]] = Field(None, description="Target group IDs")
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
                "display_ids": [1, 2],
                "cron_expression": "0 8 * * 1-5"
            }
        }


class ScheduleResponse(BaseModel):
    """Schema for Schedule response (returned by all endpoints)."""
    id: int
    name: str
    display_ids: List[int]
    group_ids: List[int]
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
                "display_ids": [1, 2, 3],
                "group_ids": [1],
                "action": "on",
                "cron_expression": "0 7 * * 1-5",
                "enabled": True,
                "created_at": "2026-01-01T08:00:00"
            }
        }
