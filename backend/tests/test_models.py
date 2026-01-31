"""
TDD: Database model tests
Tests for Display, Group, DisplayGroup, Schedule, and ScheduleExecution models.
Run these FIRST (should FAIL - RED phase), then implement models to pass them (GREEN phase).
"""

import pytest
from datetime import datetime
from app.db.models import Display, Group, DisplayGroup, Schedule, ScheduleExecution
from app.db.database import engine, SessionLocal
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session


@pytest.fixture
def db():
    """Create a fresh database session for each test."""
    # Create all tables
    from app.db.models import Base
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    session.close()
    
    # Clean up after test
    Base.metadata.drop_all(bind=engine)


class TestDisplayModel:
    """Tests for Display model - individual TV devices."""
    
    def test_create_display(self, db: Session):
        """Should create a display with all required fields."""
        display = Display(
            name="Conference Room TV",
            ip_address="192.168.1.100",
            psk="test_psk_key",
            location="Building A, Floor 3",
            tags={"type": "pro_bravia", "resolution": "4k"},
            status="active",
        )
        db.add(display)
        db.commit()
        db.refresh(display)
        
        assert display.id is not None
        assert display.name == "Conference Room TV"
        assert display.ip_address == "192.168.1.100"
        assert display.psk == "test_psk_key"
        assert display.location == "Building A, Floor 3"
        assert display.status == "active"
        assert display.tags["type"] == "pro_bravia"
        assert display.created_at is not None
        assert display.last_seen is not None
    
    def test_display_status_options(self, db: Session):
        """Should support different status values: active, standby, offline, unknown."""
        statuses = ["active", "standby", "offline", "unknown"]
        
        for status in statuses:
            display = Display(
                name=f"TV-{status}",
                ip_address=f"192.168.1.{statuses.index(status)}",
                psk="test_psk",
                status=status,
            )
            db.add(display)
        
        db.commit()
        
        retrieved = db.query(Display).all()
        assert len(retrieved) == 4
        retrieved_statuses = [d.status for d in retrieved]
        assert all(s in statuses for s in retrieved_statuses)
    
    def test_display_tags_json(self, db: Session):
        """Should store and retrieve tags as JSON."""
        tags = {
            "location_id": "room_123",
            "building": "main",
            "floor": 3,
            "resolution": "4k",
            "model": "KD-75XE9000",
        }
        
        display = Display(
            name="JSON Tags Test",
            ip_address="192.168.1.200",
            psk="psk",
            tags=tags,
        )
        db.add(display)
        db.commit()
        db.refresh(display)
        
        # Retrieve and verify
        retrieved = db.query(Display).filter_by(name="JSON Tags Test").first()
        assert retrieved.tags == tags
        assert retrieved.tags["building"] == "main"
        assert retrieved.tags["floor"] == 3
    
    def test_display_last_seen_updates(self, db: Session):
        """Should be able to update last_seen timestamp."""
        display = Display(
            name="Last Seen Test",
            ip_address="192.168.1.50",
            psk="psk",
        )
        db.add(display)
        db.commit()
        
        original_last_seen = display.last_seen
        
        # Update last_seen
        display.last_seen = datetime.utcnow()
        db.commit()
        db.refresh(display)
        
        assert display.last_seen >= original_last_seen
    
    def test_display_read_update_delete(self, db: Session):
        """Should support CRUD operations."""
        # Create
        display = Display(
            name="CRUD Test Display",
            ip_address="192.168.1.10",
            psk="psk123",
            location="Test Location",
            status="active",
        )
        db.add(display)
        db.commit()
        display_id = display.id
        
        # Read
        retrieved = db.query(Display).filter_by(id=display_id).first()
        assert retrieved is not None
        assert retrieved.name == "CRUD Test Display"
        
        # Update
        retrieved.name = "Updated Display Name"
        retrieved.status = "standby"
        db.commit()
        
        updated = db.query(Display).filter_by(id=display_id).first()
        assert updated.name == "Updated Display Name"
        assert updated.status == "standby"
        
        # Delete
        db.delete(updated)
        db.commit()
        
        deleted = db.query(Display).filter_by(id=display_id).first()
        assert deleted is None


class TestGroupModel:
    """Tests for Group model - logical groupings of displays."""
    
    def test_create_group(self, db: Session):
        """Should create a group with name and description."""
        group = Group(
            name="Conference Rooms",
            description="All conference room TVs in Building A",
        )
        db.add(group)
        db.commit()
        db.refresh(group)
        
        assert group.id is not None
        assert group.name == "Conference Rooms"
        assert group.description == "All conference room TVs in Building A"
        assert group.created_at is not None
    
    def test_group_crud(self, db: Session):
        """Should support CRUD operations on groups."""
        # Create
        group = Group(
            name="Test Group",
            description="Testing CRUD",
        )
        db.add(group)
        db.commit()
        group_id = group.id
        
        # Read
        retrieved = db.query(Group).filter_by(id=group_id).first()
        assert retrieved.name == "Test Group"
        
        # Update
        retrieved.description = "Updated description"
        db.commit()
        
        updated = db.query(Group).filter_by(id=group_id).first()
        assert updated.description == "Updated description"
        
        # Delete
        db.delete(updated)
        db.commit()
        
        deleted = db.query(Group).filter_by(id=group_id).first()
        assert deleted is None


class TestDisplayGroupModel:
    """Tests for DisplayGroup model - many-to-many relationship."""
    
    def test_add_display_to_group(self, db: Session):
        """Should add displays to a group via many-to-many relationship."""
        # Create display and group
        display = Display(
            name="Office TV",
            ip_address="192.168.1.100",
            psk="psk",
        )
        group = Group(
            name="Office Displays",
            description="Displays in office area",
        )
        db.add(display)
        db.add(group)
        db.commit()
        
        # Add display to group
        display_group = DisplayGroup(
            display_id=display.id,
            group_id=group.id,
        )
        db.add(display_group)
        db.commit()
        
        # Verify relationship
        retrieved_dg = db.query(DisplayGroup).filter_by(
            display_id=display.id,
            group_id=group.id,
        ).first()
        assert retrieved_dg is not None
    
    def test_group_with_multiple_displays(self, db: Session):
        """Should support multiple displays in one group."""
        group = Group(name="Multi Display Group")
        db.add(group)
        db.commit()
        
        # Create multiple displays
        displays = [
            Display(name=f"TV-{i}", ip_address=f"192.168.1.{i}", psk="psk")
            for i in range(1, 4)
        ]
        db.add_all(displays)
        db.commit()
        
        # Add all to group
        for display in displays:
            dg = DisplayGroup(display_id=display.id, group_id=group.id)
            db.add(dg)
        db.commit()
        
        # Verify
        group_displays = db.query(DisplayGroup).filter_by(group_id=group.id).all()
        assert len(group_displays) == 3
    
    def test_display_in_multiple_groups(self, db: Session):
        """Should support one display in multiple groups."""
        display = Display(name="Shared TV", ip_address="192.168.1.50", psk="psk")
        db.add(display)
        db.commit()
        
        # Create multiple groups
        groups = [Group(name=f"Group-{i}") for i in range(1, 4)]
        db.add_all(groups)
        db.commit()
        
        # Add display to all groups
        for group in groups:
            dg = DisplayGroup(display_id=display.id, group_id=group.id)
            db.add(dg)
        db.commit()
        
        # Verify
        display_groups = db.query(DisplayGroup).filter_by(display_id=display.id).all()
        assert len(display_groups) == 3


class TestScheduleModel:
    """Tests for Schedule model - power schedules."""
    
    def test_create_schedule_for_display(self, db: Session):
        """Should create a schedule targeting a specific display."""
        display = Display(name="Test Display", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Morning Power On",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * MON-FRI",  # 7 AM on weekdays
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        assert schedule.id is not None
        assert schedule.name == "Morning Power On"
        assert schedule.display_id == display.id
        assert schedule.group_id is None  # Not a group schedule
        assert schedule.action == "on"
        assert schedule.cron_expression == "0 7 * * MON-FRI"
        assert schedule.enabled is True
        assert schedule.created_at is not None
    
    def test_create_schedule_for_group(self, db: Session):
        """Should create a schedule targeting a group."""
        group = Group(name="Test Group")
        db.add(group)
        db.commit()
        
        schedule = Schedule(
            name="Afternoon Power Off",
            group_id=group.id,
            action="off",
            cron_expression="0 18 * * *",  # 6 PM daily
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        db.refresh(schedule)
        
        assert schedule.group_id == group.id
        assert schedule.display_id is None  # Not a display schedule
        assert schedule.action == "off"
    
    def test_schedule_action_options(self, db: Session):
        """Should support action types: 'on' and 'off'."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        for action in ["on", "off"]:
            schedule = Schedule(
                name=f"Test {action}",
                display_id=display.id,
                action=action,
                cron_expression="0 0 * * *",
                enabled=True,
            )
            db.add(schedule)
        
        db.commit()
        
        schedules = db.query(Schedule).all()
        actions = [s.action for s in schedules]
        assert "on" in actions
        assert "off" in actions
    
    def test_schedule_enable_disable(self, db: Session):
        """Should support enabling/disabling schedules."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Test Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        # Disable
        schedule.enabled = False
        db.commit()
        db.refresh(schedule)
        
        assert schedule.enabled is False
    
    def test_schedule_crud(self, db: Session):
        """Should support CRUD operations."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        # Create
        schedule = Schedule(
            name="CRUD Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        schedule_id = schedule.id
        
        # Read
        retrieved = db.query(Schedule).filter_by(id=schedule_id).first()
        assert retrieved.name == "CRUD Schedule"
        
        # Update
        retrieved.cron_expression = "0 8 * * *"
        db.commit()
        
        updated = db.query(Schedule).filter_by(id=schedule_id).first()
        assert updated.cron_expression == "0 8 * * *"
        
        # Delete
        db.delete(updated)
        db.commit()
        
        deleted = db.query(Schedule).filter_by(id=schedule_id).first()
        assert deleted is None


class TestScheduleExecutionModel:
    """Tests for ScheduleExecution model - execution logs."""
    
    def test_log_schedule_execution_success(self, db: Session):
        """Should log successful schedule execution."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Test Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            executed_at=datetime.utcnow(),
            success=True,
            error_message=None,
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        assert execution.id is not None
        assert execution.schedule_id == schedule.id
        assert execution.success is True
        assert execution.error_message is None
    
    def test_log_schedule_execution_failure(self, db: Session):
        """Should log failed schedule execution with error message."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Test Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            executed_at=datetime.utcnow(),
            success=False,
            error_message="Connection timeout: 192.168.1.100:80",
        )
        db.add(execution)
        db.commit()
        db.refresh(execution)
        
        assert execution.success is False
        assert execution.error_message == "Connection timeout: 192.168.1.100:80"
    
    def test_schedule_multiple_executions(self, db: Session):
        """Should support multiple execution logs per schedule."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Recurring Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        # Log multiple executions
        for i in range(5):
            execution = ScheduleExecution(
                schedule_id=schedule.id,
                executed_at=datetime.utcnow(),
                success=(i % 2 == 0),  # Alternate success/failure
                error_message=None if (i % 2 == 0) else "Test error",
            )
            db.add(execution)
        
        db.commit()
        
        executions = db.query(ScheduleExecution).filter_by(schedule_id=schedule.id).all()
        assert len(executions) == 5
        successful = [e for e in executions if e.success]
        failed = [e for e in executions if not e.success]
        assert len(successful) == 3
        assert len(failed) == 2
    
    def test_execution_crud(self, db: Session):
        """Should support CRUD operations on executions."""
        display = Display(name="Test", ip_address="192.168.1.1", psk="psk")
        db.add(display)
        db.commit()
        
        schedule = Schedule(
            name="Test Schedule",
            display_id=display.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        # Create
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            executed_at=datetime.utcnow(),
            success=True,
        )
        db.add(execution)
        db.commit()
        execution_id = execution.id
        
        # Read
        retrieved = db.query(ScheduleExecution).filter_by(id=execution_id).first()
        assert retrieved.success is True
        
        # Update
        retrieved.success = False
        retrieved.error_message = "Updated error"
        db.commit()
        
        updated = db.query(ScheduleExecution).filter_by(id=execution_id).first()
        assert updated.success is False
        assert updated.error_message == "Updated error"
        
        # Delete
        db.delete(updated)
        db.commit()
        
        deleted = db.query(ScheduleExecution).filter_by(id=execution_id).first()
        assert deleted is None


class TestModelIntegration:
    """Integration tests for model relationships."""
    
    def test_full_workflow(self, db: Session):
        """Should support full workflow: display → group → schedule → execution."""
        # Create display
        display = Display(
            name="Workflow Test Display",
            ip_address="192.168.1.100",
            psk="workflow_psk",
            location="Test Location",
            status="active",
        )
        db.add(display)
        db.commit()
        
        # Create group
        group = Group(
            name="Test Workflow Group",
            description="For testing",
        )
        db.add(group)
        db.commit()
        
        # Add display to group
        dg = DisplayGroup(display_id=display.id, group_id=group.id)
        db.add(dg)
        db.commit()
        
        # Create schedule for group
        schedule = Schedule(
            name="Workflow Schedule",
            group_id=group.id,
            action="on",
            cron_expression="0 7 * * *",
            enabled=True,
        )
        db.add(schedule)
        db.commit()
        
        # Log execution
        execution = ScheduleExecution(
            schedule_id=schedule.id,
            executed_at=datetime.utcnow(),
            success=True,
        )
        db.add(execution)
        db.commit()
        
        # Verify all relationships
        retrieved_display = db.query(Display).filter_by(id=display.id).first()
        assert retrieved_display is not None
        
        retrieved_group = db.query(Group).filter_by(id=group.id).first()
        assert retrieved_group is not None
        
        group_members = db.query(DisplayGroup).filter_by(group_id=group.id).all()
        assert len(group_members) == 1
        
        group_schedule = db.query(Schedule).filter_by(group_id=group.id).first()
        assert group_schedule is not None
        
        executions = db.query(ScheduleExecution).filter_by(schedule_id=schedule.id).all()
        assert len(executions) == 1
        assert executions[0].success is True
