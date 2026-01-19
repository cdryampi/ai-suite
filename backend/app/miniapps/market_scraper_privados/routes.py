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
    Run the market scraper workflow.
    Expects JSON body: {"city": "Madrid", "max_items": 10, ...}
    """
    miniapp = current_app.config.get("MARKET_SCRAPER_PRIVADOS_MINIAPP")
    if not miniapp:
        return jsonify({"error": "Mini app not initialized"}), 500

    data = request.get_json() or {}
    input_str = request.data.decode(
        "utf-8"
    )  # Pass raw JSON string or parsed? BaseMiniApp run expects string usually?
    # Checking BaseMiniApp.run signature in base.py: run(self, input_data: str, ...)
    # But in workflow.py I implemented: input_data: str.
    # So I should pass the JSON string.

    import json

    input_json_str = json.dumps(data)

    result = miniapp.run(input_data=input_json_str)

    # Convert Result to dict
    return jsonify(
        {
            "status": result.status,
            "logs": result.logs,
            "result": result.result,
            "artifacts": result.artifacts,
            "error": result.error,
        }
    )


@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Get job status."""
    job_store: JobStore = current_app.config["JOB_STORE"]
    job = job_store.get(job_id)

    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job.to_dict())
