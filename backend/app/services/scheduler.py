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

from app.db.models import Display, Schedule, ScheduleExecution, PowerLog
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
                
                self.scheduler.add_job(
                    self.execute_schedule,
                    trigger=trigger,
                    id=f"schedule_{schedule.id}",
                    args=[schedule.id],
                    replace_existing=True
                )
                
                display_count = len(schedule.schedule_displays)
                group_count = len(schedule.schedule_groups)
                targets = []
                if display_count > 0:
                    targets.append(f"{display_count} display(s)")
                if group_count > 0:
                    targets.append(f"{group_count} group(s)")
                target_str = " + ".join(targets)
                
                logger.info(
                    f"Loaded schedule '{schedule.name}' (id={schedule.id}): "
                    f"{schedule.action} {target_str} at {schedule.cron_expression}"
                )
                
            except ValueError as e:
                logger.error(
                    f"Failed to load schedule '{schedule.name}' (id={schedule.id}): {e}"
                )
                continue
    
    async def execute_schedule(self, schedule_id: int) -> None:
        """
        Execute a schedule by running the power command on target displays.
        
        Handles multiple displays and groups.
        Logs execution results to ScheduleExecution table.
        
        Args:
            schedule_id: ID of schedule to execute
        """
        logger.info(f"Executing schedule {schedule_id}")
        
        schedule = self.db.query(Schedule).filter(Schedule.id == schedule_id).first()
        
        if not schedule:
            logger.error(f"Schedule {schedule_id} not found")
            return
        
        power_on = schedule.action.lower() == "on"
        
        displays_to_control = []
        
        for schedule_display in schedule.schedule_displays:
            display = schedule_display.display
            if display:
                displays_to_control.append(display)
            else:
                logger.error(f"Display not found for schedule {schedule_id}")
        
        for schedule_group in schedule.schedule_groups:
            group = schedule_group.group
            if group:
                for dg in group.display_groups:
                    if dg.display not in displays_to_control:
                        displays_to_control.append(dg.display)
            else:
                logger.error(f"Group not found for schedule {schedule_id}")
        
        failed_displays = []
        success_count = 0
        
        try:
            for display in displays_to_control:
                logger.info(
                    f"Setting power={'ON' if power_on else 'OFF'} for display "
                    f"'{display.name}' ({display.ip_address})"
                )
                
                try:
                    result = await self.adapter.set_power(display.ip_address, display.psk, power_on)
                    
                    if result:
                        power_log = PowerLog(
                            display_id=display.id,
                            action="on" if power_on else "off",
                            timestamp=datetime.utcnow(),
                            source="schedule"
                        )
                        self.db.add(power_log)
                        success_count += 1
                    else:
                        failed_displays.append(display.name)
                        logger.error(f"Failed to execute power command on display '{display.name}'")
                except Exception as e:
                    failed_displays.append(display.name)
                    logger.error(f"Exception controlling display '{display.name}': {e}")
            
            success = len(failed_displays) == 0
            error_message = None if success else f"Failed on {len(failed_displays)} display(s): {', '.join(failed_displays)}"
            
            logger.info(
                f"Schedule {schedule_id} execution complete: "
                f"{success_count}/{len(displays_to_control)} succeeded"
            )
        
        except Exception as e:
            success = False
            error_message = f"Scheduler exception: {str(e)}"
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
