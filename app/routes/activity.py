"""Activity log routes module for tracking plug usage.

This module provides API endpoints to retrieve and manage activity logs
for smart plug operations (on/off actions with timestamps and sources).
"""

from flask import Blueprint, jsonify

from app.storage.data_manager import load_activity_log, save_activity_log

bp = Blueprint('activity', __name__, url_prefix='/api')


@bp.route("/activity_log/<plug_id>", methods=["GET"])
def get_activity_log(plug_id):
    """Get activity log entries for a specific plug.

    Args:
        plug_id (str): ID of the plug to retrieve logs for.

    Returns:
        Response: JSON array of log entries for the specified plug.
    """
    logs = load_activity_log()
    filtered = [log for log in logs if log.get("plug_id") == plug_id]
    return jsonify(filtered)


@bp.route("/activity_log/<plug_id>", methods=["DELETE"])
def clear_activity_log(plug_id):
    """Clear all activity log entries for a specific plug.

    Args:
        plug_id (str): ID of the plug to clear logs for.

    Returns:
        Response: JSON response with success status.
    """
    logs = load_activity_log()
    logs = [log for log in logs if log.get("plug_id") != plug_id]
    save_activity_log(logs)
    return jsonify({"success": True})
