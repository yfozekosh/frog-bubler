"""
Scheduler service for managing automated plug control.

Handles:
- APScheduler initialization and job management
- Loading schedules from storage on startup
- Creating cron jobs for scheduled actions
"""

import asyncio
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger("bubler.scheduler")

from app.services.tapo_device import turn_off_plug, turn_on_plug
from app.storage.data_manager import load_schedules

# Global scheduler
scheduler = BackgroundScheduler()
scheduler.start()


def schedule_job(action, hour, minute, job_id, plug_id):
    """Schedule a job to turn plug on/off at specified time"""
    if action == "on":

        def func():
            return asyncio.run(
                turn_on_plug(
                    plug_id,
                    source="automatic",
                    device_info=f"Schedule {hour:02d}:{minute:02d}",
                )
            )

    else:

        def func():
            return asyncio.run(
                turn_off_plug(
                    plug_id,
                    source="automatic",
                    device_info=f"Schedule {hour:02d}:{minute:02d}",
                )
            )

    scheduler.add_job(
        func, CronTrigger(hour=hour, minute=minute), id=job_id, replace_existing=True
    )
    logger.info("Scheduled %s for plug %s at %02d:%02d", action, plug_id, hour, minute)


def load_and_schedule():
    """Load all schedules from storage and create jobs"""
    schedules = load_schedules()
    loaded_count = 0
    for schedule in schedules:
        schedule_job(
            schedule["action"],
            schedule["hour"],
            schedule["minute"],
            schedule["id"],
            schedule.get("plug_id", "1"),
        )
        loaded_count += 1
    logger.info("Loaded %d schedule(s)", loaded_count)


def remove_job(job_id):
    """Remove a scheduled job"""
    try:
        scheduler.remove_job(job_id)
        logger.info("Removed schedule %s", job_id)
    except Exception as e:
        logger.exception("Failed to remove schedule %s: %s", job_id, e)
