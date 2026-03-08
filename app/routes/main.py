"""Main routes module for the application.

This module provides the main application routes including the home page.
"""

from flask import Blueprint, render_template

bp = Blueprint('main', __name__)


@bp.route("/")
def index():
    """Render the main application page.

    Returns:
        str: Rendered HTML template for the home page.
    """
    return render_template("index.html")
