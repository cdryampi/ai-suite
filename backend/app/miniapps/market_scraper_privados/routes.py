from flask import Blueprint, request, jsonify, current_app
from app.core.job_store import JobStore
from .workflow import MarketScraperWorkflow

bp = Blueprint(
    "market_scraper_privados",
    __name__,
    url_prefix="/api/miniapps/market_scraper_privados",
)


def init_miniapp(job_store, llm_client, tool_registry, artifact_manager):
    """
    Initialize the Market Scraper mini app.
    """
    return MarketScraperWorkflow(job_store, llm_client, tool_registry, artifact_manager)


@bp.route("/run", methods=["POST"])
def run_scraper():
    """
    Run the market scraper workflow asynchronously.
    Expects JSON body: {"city": "Madrid", "max_items": 10, ...}

    Returns immediately with job_id.
    """
    miniapp = current_app.config.get("MARKET_SCRAPER_PRIVADOS_MINIAPP")
    job_runner = current_app.config.get("JOB_RUNNER")
    job_store = current_app.config.get("JOB_STORE")

    if not miniapp or not job_runner or not job_store:
        return jsonify({"error": "System components not initialized"}), 500

    data = request.get_json() or {}

    # 1. Create Job explicitly
    job = job_store.create(
        miniapp_id=miniapp.metadata.id, input_data=data, variant=data.get("variant", 1)
    )

    # 2. Define the executor wrapper
    # The JobRunner executes this in a thread.
    # Signature: (job, on_log) -> result_dict
    def execution_wrapper(job_obj, on_log):
        # We delegate to the workflow's execute method
        # Note: We pass the 'on_log' callback so the workflow updates status real-time
        return miniapp.execute(job_obj, on_log)

    # 3. Submit to JobRunner
    try:
        job_runner.submit(job, execution_wrapper)

        return jsonify(
            {
                "status": "queued",
                "job_id": job.job_id,
                "message": "Job submitted successfully",
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Get job status."""
    job_store: JobStore = current_app.config["JOB_STORE"]
    job = job_store.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job.to_dict())


@bp.route("/jobs/<job_id>/leads", methods=["GET"])
def get_job_leads(job_id):
    """
    Get progressive leads for a specific job.
    """
    try:
        from .db import Database

        db = Database()
        leads = db.get_leads_by_job(job_id)
        return jsonify(leads)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/leads/<int:lead_id>", methods=["PATCH"])
def update_lead(lead_id):
    """
    Update a lead's status or notes.
    """
    try:
        from .db import Database

        db = Database()

        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        db.update_lead(lead_id, data)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
