"""Configuration routes for application settings.

This module provides API endpoints to retrieve and update application
configuration, including custom names for smart plugs.
"""

from flask import Blueprint, jsonify, request

from app.storage.data_manager import load_config, save_config

bp = Blueprint('config', __name__, url_prefix='/api')


@bp.route("/config", methods=["GET"])
def get_config():
    """Get the current application configuration.

    Returns:
        Response: JSON object containing application configuration.
    """
    return jsonify(load_config())


@bp.route("/config", methods=["POST"])
def update_config():
    """Update application configuration.

    Request Body:
        plug_names (dict, optional): Mapping of plug IDs to custom names.

    Returns:
        Response: JSON response containing:
            - success (bool): Whether the update succeeded
            - config (dict): The updated configuration object
    """
    config = load_config()
    data = request.json
    if "plug_names" in data:
        config["plug_names"] = data["plug_names"]
    save_config(config)
    return jsonify({"success": True, "config": config})
