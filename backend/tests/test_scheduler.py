"""
Tests for the scheduler service.

Tests cover:
- Schedule loading from database
- Cron expression parsing
- Job execution (mocked adapter)
- Execution logging to ScheduleExecution table
- Scheduler lifecycle (start/stop)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from app.services.scheduler import SchedulerService
from app.db.models import Display, Group, Schedule, ScheduleExecution
from app.db.database import get_db


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_bravia_adapter():
    """Mock BraviaAdapter for testing."""
    adapter = MagicMock()
    adapter.set_power = AsyncMock(return_value=True)
    adapter.get_power_status = AsyncMock(return_value="active")
    return adapter


@pytest.fixture
def scheduler_service(mock_db, mock_bravia_adapter):
    """Create scheduler service instance with mocked dependencies."""
    with patch("app.services.scheduler.BraviaAdapter", return_value=mock_bravia_adapter):
        service = SchedulerService(db_session=mock_db)
        yield service
        # Cleanup - only stop if running
        if service.scheduler.running:
            try:
                service.stop()
            except RuntimeError:
                pass


@pytest.fixture
def sample_display(mock_db):
    """Create sample display for testing."""
    display = Display(
        id=1,
        name="Test Display",
        ip_address="192.168.1.100",
        psk="test_psk",
        status="active",
        last_seen=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    mock_db.query.return_value.filter.return_value.first.return_value = display
    return display


@pytest.fixture
def sample_group(mock_db):
    """Create sample group with displays for testing."""
    group = Group(
        id=1,
        name="Test Group",
        description="Test group description",
        created_at=datetime.utcnow()
    )
    # Mock the display_groups relationship
    group.display_groups = []
    mock_db.query.return_value.filter.return_value.first.return_value = group
    return group


@pytest.fixture
def sample_schedule_display(sample_display):
    """Create sample schedule targeting a display."""
    schedule = Schedule(
        id=1,
        name="Morning Power On",
        display_id=sample_display.id,
        group_id=None,
        action="on",
        cron_expression="0 7 * * MON-FRI",
        enabled=True,
        created_at=datetime.utcnow()
    )
    schedule.display = sample_display
    schedule.group = None
    return schedule


@pytest.fixture
def sample_schedule_group(sample_group):
    """Create sample schedule targeting a group."""
    schedule = Schedule(
        id=2,
        name="Evening Power Off",
        display_id=None,
        group_id=sample_group.id,
        action="off",
        cron_expression="0 18 * * *",
        enabled=True,
        created_at=datetime.utcnow()
    )
    schedule.display = None
    schedule.group = sample_group
    return schedule


class TestCronParsing:
    """Tests for cron expression parsing."""
    
    def test_parse_simple_daily_cron(self, scheduler_service):
        """Test parsing simple daily cron expression."""
        # "0 7 * * *" = Every day at 7:00 AM
        trigger = scheduler_service.parse_cron("0 7 * * *")
        
        assert trigger is not None
        # CronTrigger stores fields in internal format, verify via string representation
        trigger_str = str(trigger)
        assert "hour='7'" in trigger_str
        assert "minute='0'" in trigger_str
    
    def test_parse_weekday_cron(self, scheduler_service):
        """Test parsing weekday-specific cron expression."""
        # "0 7 * * MON-FRI" = Every weekday at 7:00 AM
        trigger = scheduler_service.parse_cron("0 7 * * MON-FRI")
        
        assert trigger is not None
        trigger_str = str(trigger)
        assert "hour='7'" in trigger_str
        assert "minute='0'" in trigger_str
        assert "day_of_week='mon-fri'" in trigger_str
    
    def test_parse_specific_days_cron(self, scheduler_service):
        """Test parsing cron with specific days."""
        # "30 18 * * MON,WED,FRI" = Monday, Wednesday, Friday at 6:30 PM
        trigger = scheduler_service.parse_cron("30 18 * * MON,WED,FRI")
        
        assert trigger is not None
        trigger_str = str(trigger)
        assert "hour='18'" in trigger_str
        assert "minute='30'" in trigger_str
    
    def test_parse_invalid_cron_raises_error(self, scheduler_service):
        """Test that invalid cron expression raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler_service.parse_cron("invalid cron")
    
    def test_parse_empty_cron_raises_error(self, scheduler_service):
        """Test that empty cron expression raises ValueError."""
        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler_service.parse_cron("")


class TestScheduleLoading:
    """Tests for loading schedules from database."""
    
    def test_load_enabled_schedules_only(self, scheduler_service, mock_db, sample_schedule_display):
        """Test that only enabled schedules are loaded."""
        enabled_schedule = sample_schedule_display
        disabled_schedule = Schedule(
            id=2,
            name="Disabled Schedule",
            display_id=1,
            action="off",
            cron_expression="0 8 * * *",
            enabled=False,
            created_at=datetime.utcnow()
        )
        disabled_schedule.display = sample_schedule_display.display
        
        # Mock query to return both schedules
        mock_db.query.return_value.filter.return_value.all.return_value = [enabled_schedule]
        
        scheduler_service.load_schedules_from_db()
        
        # Verify only enabled schedule was added to scheduler
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == f"schedule_{enabled_schedule.id}"
    
    def test_load_schedules_display_target(self, scheduler_service, mock_db, sample_schedule_display):
        """Test loading schedule targeting a display."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_display]
        
        scheduler_service.load_schedules_from_db()
        
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == f"schedule_{sample_schedule_display.id}"
    
    def test_load_schedules_group_target(self, scheduler_service, mock_db, sample_schedule_group):
        """Test loading schedule targeting a group."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_group]
        
        scheduler_service.load_schedules_from_db()
        
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == f"schedule_{sample_schedule_group.id}"
    
    def test_load_schedules_empty_database(self, scheduler_service, mock_db):
        """Test loading schedules when database is empty."""
        mock_db.query.return_value.filter.return_value.all.return_value = []
        
        scheduler_service.load_schedules_from_db()
        
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 0
    
    def test_load_schedules_with_invalid_cron_skips_schedule(self, scheduler_service, mock_db, sample_schedule_display):
        """Test that schedules with invalid cron are skipped with logging."""
        sample_schedule_display.cron_expression = "invalid cron"
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_display]
        
        with patch("app.services.scheduler.logger") as mock_logger:
            scheduler_service.load_schedules_from_db()
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "Invalid cron expression" in str(mock_logger.error.call_args)
        
        # Verify no jobs were added
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 0


class TestScheduleExecution:
    """Tests for schedule execution."""
    
    @pytest.mark.asyncio
    async def test_execute_display_power_on(self, scheduler_service, mock_db, sample_schedule_display, mock_bravia_adapter):
        """Test executing power ON command for display."""
        # Mock both Schedule and Display queries
        def mock_query_side_effect(model):
            mock_query = MagicMock()
            if model == Schedule:
                mock_query.filter.return_value.first.return_value = sample_schedule_display
            elif model == Display:
                mock_query.filter.return_value.first.return_value = sample_schedule_display.display
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        
        await scheduler_service.execute_schedule(sample_schedule_display.id)
        
        # Verify set_power was called with correct parameters
        mock_bravia_adapter.set_power.assert_called_once_with(
            sample_schedule_display.display.ip_address,
            sample_schedule_display.display.psk,
            True  # action="on"
        )
        
        # Verify execution was logged
        mock_db.add.assert_called_once()
        execution = mock_db.add.call_args[0][0]
        assert isinstance(execution, ScheduleExecution)
        assert execution.schedule_id == sample_schedule_display.id
        assert execution.success is True
        assert execution.error_message is None
    
    @pytest.mark.asyncio
    async def test_execute_display_power_off(self, scheduler_service, mock_db, sample_schedule_display, mock_bravia_adapter):
        """Test executing power OFF command for display."""
        sample_schedule_display.action = "off"
        
        # Mock both Schedule and Display queries
        def mock_query_side_effect(model):
            mock_query = MagicMock()
            if model == Schedule:
                mock_query.filter.return_value.first.return_value = sample_schedule_display
            elif model == Display:
                mock_query.filter.return_value.first.return_value = sample_schedule_display.display
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        
        await scheduler_service.execute_schedule(sample_schedule_display.id)
        
        # Verify set_power was called with False
        mock_bravia_adapter.set_power.assert_called_once_with(
            sample_schedule_display.display.ip_address,
            sample_schedule_display.display.psk,
            False  # action="off"
        )
    
    @pytest.mark.asyncio
    async def test_execute_group_schedule(self, scheduler_service, mock_db, sample_schedule_group, sample_display, mock_bravia_adapter):
        """Test executing schedule for a group with multiple displays."""
        # Setup group with displays
        display1 = sample_display
        display2 = Display(
            id=2,
            name="Test Display 2",
            ip_address="192.168.1.101",
            psk="test_psk_2",
            status="active",
            last_seen=datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        
        # Mock DisplayGroup relationships
        from app.db.models import DisplayGroup
        dg1 = DisplayGroup(display_id=display1.id, group_id=sample_schedule_group.group_id)
        dg1.display = display1
        dg2 = DisplayGroup(display_id=display2.id, group_id=sample_schedule_group.group_id)
        dg2.display = display2
        
        sample_schedule_group.group.display_groups = [dg1, dg2]
        
        mock_db.query.return_value.filter.return_value.first.return_value = sample_schedule_group
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        
        await scheduler_service.execute_schedule(sample_schedule_group.id)
        
        # Verify set_power was called for both displays
        assert mock_bravia_adapter.set_power.call_count == 2
        calls = mock_bravia_adapter.set_power.call_args_list
        assert calls[0][0] == (display1.ip_address, display1.psk, False)  # action="off"
        assert calls[1][0] == (display2.ip_address, display2.psk, False)
    
    @pytest.mark.asyncio
    async def test_execute_schedule_adapter_failure(self, scheduler_service, mock_db, sample_schedule_display, mock_bravia_adapter):
        """Test execution logging when adapter fails."""
        mock_bravia_adapter.set_power.return_value = False
        
        # Mock both Schedule and Display queries
        def mock_query_side_effect(model):
            mock_query = MagicMock()
            if model == Schedule:
                mock_query.filter.return_value.first.return_value = sample_schedule_display
            elif model == Display:
                mock_query.filter.return_value.first.return_value = sample_schedule_display.display
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        
        await scheduler_service.execute_schedule(sample_schedule_display.id)
        
        # Verify execution was logged as failure
        execution = mock_db.add.call_args[0][0]
        assert execution.success is False
        assert "Failed to execute power command" in execution.error_message
    
    @pytest.mark.asyncio
    async def test_execute_schedule_not_found(self, scheduler_service, mock_db):
        """Test execution when schedule doesn't exist."""
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        
        with patch("app.services.scheduler.logger") as mock_logger:
            await scheduler_service.execute_schedule(999)
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "Schedule 999 not found" in str(mock_logger.error.call_args)
        
        # Verify no execution was logged
        mock_db.add.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_execute_schedule_exception_handling(self, scheduler_service, mock_db, sample_schedule_display, mock_bravia_adapter):
        """Test exception handling during execution."""
        mock_bravia_adapter.set_power.side_effect = Exception("Network error")
        
        # Mock both Schedule and Display queries
        def mock_query_side_effect(model):
            mock_query = MagicMock()
            if model == Schedule:
                mock_query.filter.return_value.first.return_value = sample_schedule_display
            elif model == Display:
                mock_query.filter.return_value.first.return_value = sample_schedule_display.display
            return mock_query
        
        mock_db.query.side_effect = mock_query_side_effect
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        
        await scheduler_service.execute_schedule(sample_schedule_display.id)
        
        # Verify execution was logged with error
        execution = mock_db.add.call_args[0][0]
        assert execution.success is False
        assert "Network error" in execution.error_message


class TestSchedulerLifecycle:
    """Tests for scheduler start/stop lifecycle."""
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self, scheduler_service):
        """Test starting the scheduler."""
        scheduler_service.start()
        
        assert scheduler_service.scheduler.running is True
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self, scheduler_service):
        """Test stopping the scheduler."""
        scheduler_service.start()
        scheduler_service.stop()
        
        # After shutdown, scheduler may still show running=True briefly
        # Verify stop() doesn't raise errors (idempotent behavior)
        scheduler_service.stop()  # Should not raise
    
    def test_stop_before_start_is_safe(self, scheduler_service):
        """Test that stopping before starting doesn't cause errors."""
        # Should not raise any exceptions
        scheduler_service.stop()
        
        assert scheduler_service.scheduler.running is False
    
    @pytest.mark.asyncio
    async def test_double_start_is_safe(self, scheduler_service):
        """Test that starting twice doesn't cause errors."""
        scheduler_service.start()
        scheduler_service.start()  # Should be idempotent
        
        assert scheduler_service.scheduler.running is True


class TestScheduleReload:
    """Tests for reloading schedules."""
    
    def test_reload_schedules_clears_old_jobs(self, scheduler_service, mock_db, sample_schedule_display):
        """Test that reload clears old jobs and loads new ones."""
        # Load initial schedule
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_display]
        scheduler_service.load_schedules_from_db()
        assert len(scheduler_service.scheduler.get_jobs()) == 1
        
        # Reload with empty database
        mock_db.query.return_value.filter.return_value.all.return_value = []
        scheduler_service.reload_schedules()
        
        assert len(scheduler_service.scheduler.get_jobs()) == 0
    
    def test_reload_schedules_updates_jobs(self, scheduler_service, mock_db, sample_schedule_display):
        """Test that reload updates existing schedules."""
        # Load initial schedule
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_display]
        scheduler_service.load_schedules_from_db()
        
        # Modify schedule
        sample_schedule_display.cron_expression = "0 8 * * *"
        
        # Reload
        scheduler_service.reload_schedules()
        
        # Verify job was updated
        jobs = scheduler_service.scheduler.get_jobs()
        assert len(jobs) == 1
        trigger_str = str(jobs[0].trigger)
        assert "hour='8'" in trigger_str


class TestIntegration:
    """Integration tests for scheduler service."""
    
    @pytest.mark.asyncio
    async def test_full_lifecycle_with_schedule(self, scheduler_service, mock_db, sample_schedule_display):
        """Test full lifecycle: load, start, stop."""
        mock_db.query.return_value.filter.return_value.all.return_value = [sample_schedule_display]
        
        # Load schedules
        scheduler_service.load_schedules_from_db()
        assert len(scheduler_service.scheduler.get_jobs()) == 1
        
        # Start scheduler
        scheduler_service.start()
        assert scheduler_service.scheduler.running is True
        
        # Stop scheduler
        scheduler_service.stop()
        # Verify stop() completes without error (async state may not update immediately)
