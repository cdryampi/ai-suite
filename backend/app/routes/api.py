"""
Core API endpoints - Jobs and artifacts.
"""

from flask import Blueprint

bp = Blueprint("api", __name__, url_prefix="/api")


@bp.route("/jobs/<job_id>", methods=["GET"])
def get_job(job_id: str):
    """Get job status and results."""
    return {
        "job_id": job_id,
        "status": "not_implemented",
        "message": "Job system not yet configured",
    }
