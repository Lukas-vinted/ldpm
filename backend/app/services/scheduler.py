"""
Scheduler service for LDPM application.

Manages APScheduler-based power scheduling system that:
- Loads enabled schedules from database
- Executes power commands at scheduled times
- Logs execution results to ScheduleExecution table
- Supports both display-level and group-level schedules
"""

import logging
from datetime import datetime
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.db.models import Display, Schedule, ScheduleExecution
from app.adapters.bravia import BraviaAdapter

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Scheduler service for managing power schedules.
    
    Uses APScheduler to execute power commands at scheduled times.
    Logs all execution results to the ScheduleExecution table.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize scheduler service.
        
        Args:
            db_session: SQLAlchemy database session
        """
        self.db = db_session
        self.scheduler = AsyncIOScheduler()
        self.adapter = BraviaAdapter()
        
        logger.info("SchedulerService initialized")
    
    def parse_cron(self, cron_expression: str) -> CronTrigger:
        """
        Parse cron expression into APScheduler CronTrigger.
        
        Args:
            cron_expression: Cron format string (e.g., "0 7 * * MON-FRI")
        
        Returns:
            CronTrigger instance
        
        Raises:
            ValueError: If cron expression is invalid
        """
        if not cron_expression or not cron_expression.strip():
            raise ValueError("Invalid cron expression: empty string")
        
        try:
            # Parse cron expression: "minute hour day month day_of_week"
            parts = cron_expression.strip().split()
            
            if len(parts) != 5:
                raise ValueError(f"Invalid cron expression: expected 5 fields, got {len(parts)}")
            
            minute, hour, day, month, day_of_week = parts
            
            # Create CronTrigger
            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=day_of_week
            )
            
            return trigger
            
        except Exception as e:
            raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")
    
    def load_schedules_from_db(self) -> None:
        """
        Load all enabled schedules from database and add them to scheduler.
        
        Queries for all enabled schedules and creates APScheduler jobs for each.
        Schedules with invalid cron expressions are skipped with error logging.
        """
        logger.info("Loading schedules from database")
        
        # Query all enabled schedules
        schedules = self.db.query(Schedule).filter(Schedule.enabled == True).all()  # noqa: E712
        
        logger.info(f"Found {len(schedules)} enabled schedule(s)")
        
        for schedule in schedules:
            try:
                # Parse cron expression
                trigger = self.parse_cron(schedule.cron_expression)
                
                # Add job to scheduler
                self.scheduler.add_job(
                    self.execute_schedule,
                    trigger=trigger,
                    id=f"schedule_{schedule.id}",
                    args=[schedule.id],
                    replace_existing=True
                )
                
                target_type = "display" if schedule.display_id else "group"
                target_id = schedule.display_id or schedule.group_id
                
                logger.info(
                    f"Loaded schedule '{schedule.name}' (id={schedule.id}): "
                    f"{schedule.action} {target_type} {target_id} at {schedule.cron_expression}"
                )
                
            except ValueError as e:
                logger.error(
                    f"Failed to load schedule '{schedule.name}' (id={schedule.id}): {e}"
                )
                continue
    
    async def execute_schedule(self, schedule_id: int) -> None:
        """
        Execute a schedule by running the power command on target displays.
        
        Handles both display-level and group-level schedules.
        Logs execution results to ScheduleExecution table.
        
        Args:
            schedule_id: ID of schedule to execute
        """
        logger.info(f"Executing schedule {schedule_id}")
        
        # Fetch schedule from database
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        # Determine power state from action
        power_on = schedule.action.lower() == "on"
        
        # Collect displays to control
        displays_to_control = []
        
        if schedule.display_id:
            # Single display schedule
            display = self.db.query(Display).filter(Display.id == schedule.display_id).first()
            if display:
                displays_to_control.append(display)
            else:
                logger.error(f"Display {schedule.display_id} not found for schedule {schedule_id}")
        
        elif schedule.group_id:
            # Group schedule - get all displays in group
            for dg in schedule.group.display_groups:
                displays_to_control.append(dg.display)
        
        # Execute power commands
        success = True
        error_message = None
        
        try:
            for display in displays_to_control:
                logger.info(
                    f"Setting power={'ON' if power_on else 'OFF'} for display "
                    f"'{display.name}' ({display.ip_address})"
                )
                
                result = await self.adapter.set_power(display.ip_address, display.psk, power_on)
                
                if not result:
                    success = False
                    error_message = f"Failed to execute power command on display '{display.name}'"
                    logger.error(error_message)
                    break
            
            if success:
                logger.info(f"Successfully executed schedule {schedule_id}")
        
        except Exception as e:
            success = False
            error_message = str(e)
            logger.error(f"Exception during schedule {schedule_id} execution: {e}")
        
        # Log execution to database
        execution = ScheduleExecution(
            schedule_id=schedule_id,
            executed_at=datetime.utcnow(),
            success=success,
            error_message=error_message
        )
        
        self.db.add(execution)
        self.db.commit()
        
        logger.info(
            f"Logged execution for schedule {schedule_id}: "
            f"success={success}, error={error_message}"
        )
    
    def reload_schedules(self) -> None:
        """
        Reload schedules from database.
        
        Removes all existing jobs and reloads from database.
        Useful when schedules are modified through the API.
        """
        logger.info("Reloading schedules")
        
        # Remove all existing jobs
        self.scheduler.remove_all_jobs()
        
        # Reload from database
        self.load_schedules_from_db()
        
        logger.info("Schedules reloaded")
    
    def start(self) -> None:
        """
        Start the scheduler.
        
        Begins executing scheduled jobs.
        Safe to call multiple times (idempotent).
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler started")
        else:
            logger.debug("Scheduler already running")
    
    def stop(self) -> None:
        """
        Stop the scheduler.
        
        Stops executing scheduled jobs.
        Safe to call multiple times (idempotent).
        """
        if self.scheduler.running:
            try:
                self.scheduler.shutdown(wait=False)
                logger.info("Scheduler stopped")
            except RuntimeError:
                logger.debug("Event loop closed, scheduler already stopped")
        else:
            logger.debug("Scheduler already stopped")
