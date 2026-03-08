"""Schedule management routes for automated plug control.

This module provides API endpoints to create, retrieve, and delete
scheduled tasks for automatic plug on/off operations at specified times.
"""

from datetime import datetime

from flask import Blueprint, jsonify, request

from app.services.scheduler import remove_job, schedule_job
from app.storage.data_manager import load_schedules, save_schedules

bp = Blueprint('schedules', __name__, url_prefix='/api')


@bp.route("/schedules/<plug_id>", methods=["GET"])
def get_schedules(plug_id):
    """Get all schedules for a specific plug.

    Args:
        plug_id (str): ID of the plug to retrieve schedules for.

    Returns:
        Response: JSON array of schedule objects for the specified plug.
    """
    schedules = load_schedules()
    filtered = [s for s in schedules if s.get("plug_id", "1") == plug_id]
    return jsonify(filtered)


@bp.route("/schedules/<plug_id>", methods=["POST"])
def add_schedule(plug_id):
    """Create a new schedule for a plug.

    Args:
        plug_id (str): ID of the plug to schedule.

    Request Body:
        action (str): Action to perform ("on" or "off").
        hour (int): Hour of the day (0-23).
        minute (int): Minute of the hour (0-59).

    Returns:
        Response: JSON response containing:
            - success (bool): Whether the schedule was created
            - schedule (dict): The newly created schedule object
    """
    data = request.json
    schedules = load_schedules()

    schedule_id = f"schedule_{plug_id}_{len(schedules)}_{datetime.now().timestamp()}"
    new_schedule = {
        "id": schedule_id,
        "plug_id": plug_id,
        "action": data["action"],
        "hour": data["hour"],
        "minute": data["minute"],
    }

    schedules.append(new_schedule)
    save_schedules(schedules)

    schedule_job(data["action"], data["hour"], data["minute"], schedule_id, plug_id)

    return jsonify({"success": True, "schedule": new_schedule})


@bp.route("/schedules/<plug_id>/<schedule_id>", methods=["DELETE"])
def delete_schedule(plug_id, schedule_id):
    """Delete a specific schedule.

    Args:
        plug_id (str): ID of the plug (for URL routing).
        schedule_id (str): ID of the schedule to delete.

    Returns:
        Response: JSON response with success status.
    """
    schedules = load_schedules()
    schedules = [s for s in schedules if s["id"] != schedule_id]
    save_schedules(schedules)
    remove_job(schedule_id)
    return jsonify({"success": True})
