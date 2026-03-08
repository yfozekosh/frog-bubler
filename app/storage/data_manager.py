"""Data persistence manager for schedules, configuration, and activity logs.

This module provides functions to load and save application data to JSON files:
- Schedule management for plug automation
- Application configuration including plug names
- Activity logging for plug state changes
"""

import json
import os
from datetime import datetime

from app.config import ACTIVITY_LOG_FILE, CONFIG_FILE, SCHEDULE_FILE


def load_schedules():
    """Load scheduled tasks from storage.

    Returns:
        list: List of schedule dictionaries, or empty list if file doesn't exist.
    """
    if os.path.exists(SCHEDULE_FILE):
        with open(SCHEDULE_FILE, "r") as f:
            return json.load(f)
    return []


def save_schedules(schedules):
    """Save scheduled tasks to storage.

    Args:
        schedules (list): List of schedule dictionaries to save.
    """
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedules, f)


def load_config():
    """Load application configuration from storage.

    Returns:
        dict: Configuration dictionary with plug names and settings.
              Returns default config if file doesn't exist.
    """
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"plug_names": {"1": "Plug 1", "2": "Plug 2"}}


def save_config(config):
    """Save application configuration to storage.

    Args:
        config (dict): Configuration dictionary to save.
    """
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)


def load_activity_log():
    """Load activity log from storage.

    Returns:
        list: List of log entry dictionaries, or empty list if file doesn't exist.
    """
    if os.path.exists(ACTIVITY_LOG_FILE):
        with open(ACTIVITY_LOG_FILE, "r") as f:
            return json.load(f)
    return []


def save_activity_log(logs):
    """Save activity log to storage.

    Args:
        logs (list): List of log entry dictionaries to save.
    """
    os.makedirs(os.path.dirname(ACTIVITY_LOG_FILE), exist_ok=True)
    with open(ACTIVITY_LOG_FILE, "w") as f:
        json.dump(logs, f)


def add_activity_log(plug_id, action, source="manual", device_info=None):
    """Add a new entry to the activity log.

    Args:
        plug_id (str): ID of the plug (e.g., "1" or "2").
        action (str): Action performed (e.g., "on" or "off").
        source (str, optional): Source of the action. Defaults to "manual".
        device_info (str, optional): Information about the device/user.
                                     Defaults to None.

    Returns:
        dict: The newly created log entry.
    """
    logs = load_activity_log()
    log_entry = {
        "plug_id": plug_id,
        "action": action,
        "source": source,
        "timestamp": datetime.now().isoformat(),
        "device_info": device_info
    }
    logs.insert(0, log_entry)
    save_activity_log(logs)
    return log_entry
