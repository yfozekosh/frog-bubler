"""Energy monitoring endpoints"""

from datetime import datetime
from typing import Any

from app import logger
from app.services.tapo_device import get_device
from flask import Blueprint, jsonify
from tapo.requests import EnergyDataInterval

bp = Blueprint("energy", __name__, url_prefix="/api")


@bp.route("/energy/day/<plug_id>")
async def get_energy_day(plug_id):
    """Get today's energy usage in Wh"""
    try:
        device = await get_device(plug_id)
        # device may be None if credentials missing — handled by get_device which now raises
        energy_data: Any = await device.get_energy_data(interval=EnergyDataInterval.Hourly)

        total = sum(getattr(energy_data, "data", []) or [])
        return jsonify({"success": True, "energy": total})  # Wh
    except RuntimeError as e:
        logger.warning("Configuration error getting daily energy for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error getting daily energy for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 500


@bp.route("/energy/month/<plug_id>")
async def get_energy_month(plug_id):
    """Get this month's energy usage in Wh"""
    try:
        device = await get_device(plug_id)
        now = datetime.now()
        energy_data: Any = await device.get_energy_data(
            interval=EnergyDataInterval.Daily,
            start_date=datetime(now.year, now.month, 1),
        )

        total = sum(getattr(energy_data, "data", []) or [])
        return jsonify({"success": True, "energy": total})  # Wh
    except RuntimeError as e:
        logger.warning("Configuration error getting monthly energy for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        logger.exception("Error getting monthly energy for plug %s: %s", plug_id, e)
        return jsonify({"success": False, "error": str(e)}), 500
