"""Status routes module for device information endpoints.

This module provides API endpoints to retrieve the current status
and power information of Tapo smart plugs.
"""

from flask import Blueprint, jsonify
from app import logger

from app.services.tapo_device import get_device

bp = Blueprint('status', __name__, url_prefix='/api')


@bp.route("/status/<plug_id>")
async def get_status(plug_id):
    """Get the current status and power consumption of a plug.

    Args:
        plug_id (str): ID of the plug to query.

    Returns:
        Response: JSON response containing:
            - success (bool): Whether the request succeeded
            - is_on (bool): Whether the plug is currently on
            - current_power (float): Current power consumption in watts
            - error (str): Error message if request failed (only on failure)
    """
    try:
        device = await get_device(plug_id)
        info = await device.get_device_info()
        energy = await device.get_current_power()

        result = {
            "success": True,
            "is_on": getattr(info, "device_on", False),
            "current_power": getattr(energy, "current_power", 0.0),
        }
        return jsonify(result)
    except RuntimeError as e:
        # Likely missing TAPO credentials — return clear client error
        logger.warning("Configuration error in get_status for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error in get_status for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 500
