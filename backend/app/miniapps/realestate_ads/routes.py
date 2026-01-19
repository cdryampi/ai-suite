"""
API routes for the Real Estate Ad Generator mini app.

Provides endpoints for:
- Running the ad generation workflow
- Checking job status
- Retrieving artifacts

Routes:
    POST /api/miniapps/realestate_ads/run - Start ad generation
    GET /api/miniapps/realestate_ads/status/<job_id> - Check job status
    GET /api/miniapps/realestate_ads/artifact/<job_id>/<filename> - Get artifact
"""

from flask import Blueprint, request, jsonify, send_file
from pathlib import Path

from ...core.job_store import JobStore
from ...core.llm_client import LLMClient
from ...core.tool_registry import ToolRegistry
from ...core.artifacts import ArtifactManager
from .workflow import RealEstateAdGenerator

# Create blueprint
bp = Blueprint("realestate_ads", __name__, url_prefix="/api/miniapps/realestate_ads")


def init_miniapp(
    job_store: JobStore,
    llm_client: LLMClient,
    tool_registry: ToolRegistry,
    artifact_manager: ArtifactManager,
):
    """
    Initialize the mini app with dependencies.

    This should be called from the Flask app factory.

    Args:
        job_store: JobStore instance
        llm_client: LLMClient instance
        tool_registry: ToolRegistry instance
        artifact_manager: ArtifactManager instance

    Returns:
        RealEstateAdGenerator instance
    """
    return RealEstateAdGenerator(job_store, llm_client, tool_registry, artifact_manager)


@bp.route("/run", methods=["POST"])
def run():
    """
    Start the ad generation workflow.

    Request JSON:
    {
        "input": "https://example.com/listing",
        "variant": 1,
        "options": {}
    }

    Response JSON:
    {
        "status": "ok|error",
        "job_id": "string",
        "logs": ["string"],
        "artifacts": [
            {"type": "text|json", "label": "string", "path": "string"}
        ],
        "result": {},
        "error": "string (optional)"
    }
    """
    try:
        data = request.get_json()

        # Validate request
        if not data:
            return jsonify({"status": "error", "error": "No JSON data provided"}), 400

        input_url = data.get("input")
        if not input_url:
            return jsonify(
                {"status": "error", "error": "Missing 'input' field (URL required)"}
            ), 400

        variant = data.get("variant", 1)
        options = data.get("options", {})

        # Get mini app instance from app context
        miniapp = request.current_app.config.get("REALESTATE_ADS_MINIAPP")
        if not miniapp:
            return jsonify(
                {"status": "error", "error": "Mini app not initialized"}
            ), 500

        # Run the workflow
        result = miniapp.run(input_data=input_url, variant=variant, options=options)

        # Convert result to dict
        response = {
            "status": result.status,
            "job_id": result.result.get("job_id"),
            "logs": result.logs,
            "artifacts": result.artifacts,
            "result": result.result,
        }

        if result.error:
            response["error"] = result.error

        if result.execution_time:
            response["execution_time"] = result.execution_time

        status_code = 200 if result.status == "ok" else 500
        return jsonify(response), status_code

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """
    Get the status of a job.

    Args:
        job_id: Job ID

    Response JSON:
    {
        "job_id": "string",
        "status": "PENDING|RUNNING|COMPLETE|FAILED|CANCELLED",
        "created_at": "ISO datetime",
        "logs": ["string"],
        "error": "string (optional)"
    }
    """
    try:
        # Get job store from app context
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
        }

        if job.error:
            response["error"] = job.error

        if job.completed_at:
            response["completed_at"] = job.completed_at.isoformat()

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/artifact/<job_id>/<path:filename>", methods=["GET"])
def get_artifact(job_id, filename):
    """
    Download an artifact file.

    Args:
        job_id: Job ID
        filename: Artifact filename

    Returns:
        File download
    """
    try:
        # Get artifact manager from app context
        artifact_manager = request.current_app.config.get("ARTIFACT_MANAGER")
        if not artifact_manager:
            return jsonify(
                {"status": "error", "error": "Artifact manager not initialized"}
            ), 500

        # Get artifact path
        artifact_path = artifact_manager.get_artifact_path(job_id, filename)

        if not Path(artifact_path).exists():
            return jsonify({"status": "error", "error": "Artifact not found"}), 404

        return send_file(artifact_path, as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@bp.route("/info", methods=["GET"])
def get_info():
    """
    Get mini app metadata.

    Response JSON:
    {
        "id": "realestate_ads",
        "name": "Real Estate Ad Generator",
        "description": "...",
        "version": "1.0.0",
        "variants": {
            "1": "Basic - Simple, concise ad",
            "2": "Detailed - Comprehensive, sophisticated ad",
            "3": "SEO-optimized - Search engine optimized ad"
        }
    }
    """
    try:
        miniapp = request.current_app.config.get("REALESTATE_ADS_MINIAPP")
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
                "author": metadata.author,
                "tags": metadata.tags,
                "variants": metadata.variants,
            }
        ), 200

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500
