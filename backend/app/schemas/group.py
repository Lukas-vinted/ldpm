"""
Pydantic schemas for Group API endpoints.

Schemas:
- GroupCreate: Request body for POST /api/v1/groups
- GroupUpdate: Request body for PUT /api/v1/groups/{id}
- GroupResponse: Response model for Group objects
- AddDisplaysRequest: Request body for POST /api/v1/groups/{id}/displays
- RemoveDisplaysRequest: Request body for DELETE /api/v1/groups/{id}/displays
- BulkPowerRequest: Request body for POST /api/v1/groups/{id}/power
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GroupCreate(BaseModel):
    """Schema for creating a new group."""
    name: str = Field(..., min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, description="Group description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Conference Rooms",
                "description": "All conference room displays"
            }
        }


class GroupUpdate(BaseModel):
    """Schema for updating an existing group."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Group name")
    description: Optional[str] = Field(None, description="Group description")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Conference Rooms",
                "description": "Updated description"
            }
        }


class GroupResponse(BaseModel):
    """Schema for Group response (returned by all endpoints)."""
    id: int
    name: str
    description: Optional[str]
    created_at: datetime
    display_count: int = Field(default=0, description="Number of displays in this group")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Conference Rooms",
                "description": "All conference room displays",
                "created_at": "2026-01-01T08:00:00",
                "display_count": 5
            }
        }


class AddDisplaysRequest(BaseModel):
    """Schema for adding displays to a group."""
    display_ids: List[int] = Field(..., min_length=1, description="List of display IDs to add")

    class Config:
        json_schema_extra = {
            "example": {
                "display_ids": [1, 2, 3]
            }
        }


class RemoveDisplaysRequest(BaseModel):
    """Schema for removing displays from a group."""
    display_ids: List[int] = Field(..., min_length=1, description="List of display IDs to remove")

    class Config:
        json_schema_extra = {
            "example": {
                "display_ids": [1, 2]
            }
        }


class BulkPowerRequest(BaseModel):
    """Schema for bulk power control request."""
    on: bool = Field(..., description="True to power on all displays, False to power off")

    class Config:
        json_schema_extra = {
            "example": {
                "on": True
            }
        }


class BulkPowerResponse(BaseModel):
    """Schema for bulk power control response."""
    group_id: int
    total_displays: int
    successful: int
    failed: int
    results: List[dict] = Field(default_factory=list, description="Per-display results")

    class Config:
        json_schema_extra = {
            "example": {
                "group_id": 1,
                "total_displays": 5,
                "successful": 4,
                "failed": 1,
                "results": [
                    {"display_id": 1, "success": True},
                    {"display_id": 2, "success": True},
                    {"display_id": 3, "success": False, "error": "Connection timeout"}
                ]
            }
        }
