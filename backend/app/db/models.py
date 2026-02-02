"""
SQLAlchemy ORM models for LDPM application.

Models:
- Display: Individual Sony BRAVIA TV with network information
- Group: Logical grouping of displays
- DisplayGroup: Many-to-many junction table for Display ↔ Group
- Schedule: Power schedule that targets displays or groups
- ScheduleExecution: Execution log for schedule runs
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base


class Display(Base):
    """
    Display model - represents a Sony BRAVIA Pro TV.
    
    Attributes:
        id: Primary key
        name: Display name (e.g., "Conference Room TV")
        ip_address: Network IP address (e.g., "192.168.1.100")
        psk: Pre-Shared Key for authentication (plain text for v1 - TECHNICAL DEBT: encrypt in v2)
        location: Physical location description
        tags: JSON field for flexible tagging ({"building": "A", "floor": 3, "type": "pro_bravia"})
        status: Current status - "active", "standby", "offline", or "unknown"
        last_seen: Timestamp of last successful communication
        created_at: Timestamp when display was added to system
    """
    __tablename__ = "displays"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    ip_address = Column(String(255), nullable=False, unique=True, index=True)
    psk = Column(String(255), nullable=True)  # Optional - Simple IP Control doesn't require auth
    location = Column(String(255), nullable=True)
    tags = Column(JSON, nullable=True, default={})
    status = Column(String(50), nullable=False, default="unknown")  # active|standby|offline|unknown
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    display_groups = relationship("DisplayGroup", back_populates="display", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="display", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Display(id={self.id}, name={self.name}, ip={self.ip_address}, status={self.status})>"


class Group(Base):
    """
    Group model - logical grouping of displays.
    
    Attributes:
        id: Primary key
        name: Group name (e.g., "Conference Rooms", "Lobbies")
        description: Optional description
        created_at: Timestamp when group was created
    """
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    display_groups = relationship("DisplayGroup", back_populates="group", cascade="all, delete-orphan")
    schedules = relationship("Schedule", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Group(id={self.id}, name={self.name})>"


class DisplayGroup(Base):
    """
    DisplayGroup model - many-to-many junction table for Display ↔ Group.
    
    Allows a display to belong to multiple groups and a group to contain multiple displays.
    
    Attributes:
        display_id: Foreign key to Display
        group_id: Foreign key to Group
    """
    __tablename__ = "display_groups"
    
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True)
    
    # Relationships
    display = relationship("Display", back_populates="display_groups")
    group = relationship("Group", back_populates="display_groups")
    
    def __repr__(self):
        return f"<DisplayGroup(display_id={self.display_id}, group_id={self.group_id})>"


class Schedule(Base):
    """
    Schedule model - power control schedule for displays or groups.
    
    A schedule targets EITHER a single display OR a group (one of display_id/group_id is null).
    Uses cron expressions for flexibility (e.g., "0 7 * * MON-FRI" = 7 AM on weekdays).
    
    Attributes:
        id: Primary key
        name: Schedule name (e.g., "Morning Power On", "Evening Shutdown")
        display_id: Foreign key to Display (null if targeting group)
        group_id: Foreign key to Group (null if targeting display)
        action: Power action - "on" or "off"
        cron_expression: Cron format string (e.g., "0 7 * * *" for 7 AM daily)
        enabled: Whether schedule is active
        created_at: Timestamp when schedule was created
    """
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(10), nullable=False)  # "on" or "off"
    cron_expression = Column(String(255), nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    display = relationship("Display", back_populates="schedules")
    group = relationship("Group", back_populates="schedules")
    executions = relationship("ScheduleExecution", back_populates="schedule", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Schedule(id={self.id}, name={self.name}, action={self.action}, enabled={self.enabled})>"


class ScheduleExecution(Base):
    """
    ScheduleExecution model - execution log for schedule runs.
    
    Records each time a schedule is executed, including success/failure status and error messages.
    
    Attributes:
        id: Primary key
        schedule_id: Foreign key to Schedule
        executed_at: When the schedule was executed
        success: Whether execution succeeded
        error_message: Error message if execution failed (null if success=True)
    """
    __tablename__ = "schedule_executions"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="CASCADE"), nullable=False, index=True)
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    schedule = relationship("Schedule", back_populates="executions")
    
    def __repr__(self):
        return f"<ScheduleExecution(id={self.id}, schedule_id={self.schedule_id}, success={self.success})>"


class PowerLog(Base):
    """
    PowerLog model - tracks power state changes for energy savings calculation.
    
    Records every power on/off event to calculate total time displays were off
    and estimate energy savings.
    
    Attributes:
        id: Primary key
        display_id: Foreign key to Display
        action: Power action - "on" or "off"
        timestamp: When the power state changed
        source: Source of change - "manual", "schedule", or "api"
    """
    __tablename__ = "power_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    display_id = Column(Integer, ForeignKey("displays.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(10), nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    source = Column(String(50), nullable=False, default="manual")
    
    # Relationships
    display = relationship("Display")
    
    def __repr__(self):
        return f"<PowerLog(id={self.id}, display_id={self.display_id}, action={self.action}, timestamp={self.timestamp})>"
