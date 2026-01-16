"""
Health check endpoints.
"""

from flask import Blueprint, current_app

bp = Blueprint("health", __name__, url_prefix="/api/health")


@bp.route("", methods=["GET"])
def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "version": "0.1.0", "llm_connected": False}


@bp.route("/llm", methods=["GET"])
def llm_health():
    """LLM connection health check."""
    settings = current_app.config.get("SETTINGS")

    return {
        "status": "not_configured",
        "provider": settings.llm.provider if settings else "unknown",
        "base_url": settings.llm.base_url if settings else "unknown",
    }
