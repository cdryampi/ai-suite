"""
Mini apps listing endpoints.
"""

from flask import Blueprint

bp = Blueprint("miniapps_list", __name__, url_prefix="/api/miniapps")


@bp.route("", methods=["GET"])
def list_miniapps():
    """List all registered mini apps."""
    return {"miniapps": []}
