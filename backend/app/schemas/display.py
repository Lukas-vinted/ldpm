"""
Pydantic schemas for Display API endpoints.

Schemas:
- DisplayCreate: Request body for POST /api/v1/displays
- DisplayUpdate: Request body for PUT /api/v1/displays/{id}
- DisplayResponse: Response model for Display objects
- PowerRequest: Request body for POST /api/v1/displays/{id}/power
- PowerStatusResponse: Response model for GET /api/v1/displays/{id}/status
"""

from pydantic import BaseModel, Field, IPvAnyAddress
from typing import Optional, Dict, Any, List
from datetime import datetime


class DisplayCreate(BaseModel):
    """Schema for creating a new display."""
    name: str = Field(..., min_length=1, max_length=255, description="Display name")
    ip_address: str = Field(..., description="IP address of the display")
    psk: Optional[str] = Field(None, max_length=255, description="Pre-Shared Key for authentication (optional - only needed for REST API)")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    tags: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Flexible JSON tags")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Conference Room TV",
                "ip_address": "192.168.1.100",
                "psk": "my_secret_psk",
                "location": "Building A - Floor 2 - Room 201",
                "tags": {"building": "A", "floor": 2, "type": "pro_bravia"}
            }
        }


class DisplayUpdate(BaseModel):
    """Schema for updating an existing display."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Display name")
    ip_address: Optional[str] = Field(None, description="IP address of the display")
    psk: Optional[str] = Field(None, max_length=255, description="Pre-Shared Key")
    location: Optional[str] = Field(None, max_length=255, description="Physical location")
    tags: Optional[Dict[str, Any]] = Field(None, description="Flexible JSON tags")
    status: Optional[str] = Field(None, description="Current status")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Updated Conference Room TV",
                "location": "Building B - Floor 3"
            }
        }


class DisplayResponse(BaseModel):
    """Schema for Display response (returned by all endpoints)."""
    id: int
    name: str
    ip_address: str
    psk: Optional[str]
    location: Optional[str]
    tags: Dict[str, Any]
    status: str
    last_seen: datetime
    created_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLAlchemy models
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Conference Room TV",
                "ip_address": "192.168.1.100",
                "psk": "my_secret_psk",
                "location": "Building A - Floor 2 - Room 201",
                "tags": {"building": "A", "floor": 2},
                "status": "active",
                "last_seen": "2026-01-31T12:00:00",
                "created_at": "2026-01-01T08:00:00"
            }
        }


class PowerRequest(BaseModel):
    """Schema for power control request."""
    on: bool = Field(..., description="True to power on, False to power off")

    class Config:
        json_schema_extra = {
            "example": {
                "on": True
            }
        }


class PowerStatusResponse(BaseModel):
    """Schema for power status response."""
    display_id: int
    status: str = Field(..., description="Power status: active, standby, or error")
    last_checked: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "display_id": 1,
                "status": "active",
                "last_checked": "2026-01-31T12:00:00"
            }
        }


class CSVImportRowError(BaseModel):
    """Schema for a failed CSV row import."""
    row_number: int
    data: Dict[str, Any]
    error: str

    class Config:
        json_schema_extra = {
            "example": {
                "row_number": 5,
                "data": {"ip_address": "invalid.ip", "name": "TV-5", "location": ""},
                "error": "Invalid IP address format"
            }
        }


class CSVImportResponse(BaseModel):
    """Schema for CSV import response."""
    created_count: int = Field(..., description="Number of new displays created")
    updated_count: int = Field(..., description="Number of existing displays updated")
    failed_count: int = Field(..., description="Number of rows that failed to import")
    total_processed: int = Field(..., description="Total rows processed")
    failed_rows: List[CSVImportRowError] = Field(default_factory=list, description="Details of failed rows")

    class Config:
        json_schema_extra = {
            "example": {
                "created_count": 8,
                "updated_count": 2,
                "failed_count": 1,
                "total_processed": 11,
                "failed_rows": [
                    {
                        "row_number": 5,
                        "data": {"ip_address": "invalid.ip", "name": "TV-5", "location": ""},
                        "error": "Invalid IP address format"
                    }
                ]
            }
        }
