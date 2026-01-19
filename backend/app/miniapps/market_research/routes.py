"""
API routes for the Market Research mini app.
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path

from ...core.job_store import JobStore
from ...core.llm_client import LLMClient
from ...core.tool_registry import ToolRegistry
from ...core.artifacts import ArtifactManager
from .workflow import MarketResearchWorkflow

# Create blueprint
bp = Blueprint("market_research", __name__, url_prefix="/api/miniapps/market_research")


def init_miniapp(
    job_store: JobStore,
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
    artifact_manager: ArtifactManager,
):
    return MarketResearchWorkflow(
        job_store, llm_client, tool_registry, artifact_manager
    )


@bp.route("/run", methods=["POST"])
def run():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400

        input_data = data.get("input")
        if not input_data:
            return jsonify(
                {"status": "error", "error": "Missing 'input' field (topic required)"}
            ), 400

        variant = data.get("variant", 1)
        options = data.get("options", {})

        miniapp = request.current_app.config.get("MARKET_RESEARCH_MINIAPP")
        if not miniapp:
            return jsonify(
                {"status": "error", "error": "Mini app not initialized"}
            ), 500

        result = miniapp.run(input_data=input_data, variant=variant, options=options)

        response = {
            "status": result.status,
            "job_id": result.result.get("job_id") if result.result else None,
            "logs": result.logs,
            "artifacts": result.artifacts,
            "result": result.result,
        }

        if result.error:
            response["error"] = result.error

        return jsonify(response), 200 if result.status == "ok" else 500

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    try:
        job_store = request.current_app.config.get("JOB_STORE")
        if not job_store:
            return jsonify(
                {"status": "error", "error": "Job store not initialized"}
            ), 500

        job = job_store.get(job_id)
        if not job:
            return jsonify({"status": "error", "error": "Job not found"}), 404

        response = {
            "job_id": job.id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "logs": job.logs,
            # Include artifacts in status response to make polling easier
            "artifacts": [
                {
                    "type": a.type,
                    "label": a.label,
                    "path": str(a.path).replace(
                        "\\", "/"
                    ),  # Normalize path for consistency
                    "filename": a.filename,
                }
                for a in request.current_app.config.get(
                    "ARTIFACT_MANAGER"
                ).list_artifacts(job.id)
            ],
        }

        if job.error:
            response["error"] = job.error

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/artifact/<job_id>/<path:filename>", methods=["GET"])
def get_artifact(job_id, filename):
    try:
        artifact_manager = request.current_app.config.get("ARTIFACT_MANAGER")
        if not artifact_manager:
            return jsonify(
                {"status": "error", "error": "Artifact manager not initialized"}
            ), 500

        artifact_path = artifact_manager.get_artifact_path(job_id, filename)

        if not Path(artifact_path).exists():
            return jsonify({"status": "error", "error": "Artifact not found"}), 404

        return send_file(artifact_path, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/info", methods=["GET"])
def get_info():
    try:
        miniapp = request.current_app.config.get("MARKET_RESEARCH_MINIAPP")
        if not miniapp:
            return jsonify(
                {"status": "error", "error": "Mini app not initialized"}
            ), 500

        metadata = miniapp.metadata

        return jsonify(
            {
                "id": metadata.id,
                "name": metadata.name,
                "description": metadata.description,
                "version": metadata.version,
                "tags": metadata.tags,
                "variants": metadata.variants,
            }
        ), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
