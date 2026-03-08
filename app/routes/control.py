"""Control routes for manual plug operations.

This module provides API endpoints to manually control smart plugs
(turn on/off) with device tracking for activity logging.
"""

from app import logger
from app.services.tapo_device import turn_off_plug, turn_on_plug
from flask import Blueprint, jsonify, request

bp = Blueprint('control', __name__, url_prefix='/api')


@bp.route("/turn_on/<plug_id>", methods=["POST"])
async def turn_on(plug_id):
    """Turn on a smart plug.

    Args:
        plug_id (str): ID of the plug to turn on.

    Returns:
        Response: JSON response containing:
            - success (bool): Whether the operation succeeded
            - error (str): Error message if request failed (only on failure)
    """
    try:
        device_info = request.headers.get('User-Agent', 'Unknown')
        ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
        device_info = f"{ip_addr} - {device_info[:50]}"
        await turn_on_plug(plug_id, source="manual", device_info=device_info)
        return jsonify({"success": True})
    except RuntimeError as e:
        logger.warning("Configuration error in turn_on for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in turn_on for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/turn_off/<plug_id>", methods=["POST"])
async def turn_off(plug_id):
    """Turn off a smart plug.

    Args:
        plug_id (str): ID of the plug to turn off.

    Returns:
        Response: JSON response containing:
            - success (bool): Whether the operation succeeded
            - error (str): Error message if request failed (only on failure)
    """
    try:
        device_info = request.headers.get('User-Agent', 'Unknown')
        ip_addr = request.headers.get('X-Forwarded-For', request.remote_addr)
        device_info = f"{ip_addr} - {device_info[:50]}"
        await turn_off_plug(plug_id, source="manual", device_info=device_info)
        return jsonify({"success": True})
    except RuntimeError as e:
        logger.warning("Configuration error in turn_off for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in turn_off for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 500
