"""
Mini App Registry - Central registration.
"""

from flask import Flask


MINIAPPS = {}


def get_all_miniapps() -> dict:
    """Get all registered mini apps."""
    return MINIAPPS


def get_miniapp(app_id: str):
    """Get a specific mini app by ID."""
    return MINIAPPS.get(app_id)


def register_miniapps(app: Flask) -> None:
    """Register all mini app blueprints and initialize mini apps."""
    from pathlib import Path
    from app.core.artifacts import ArtifactManager
    from app.miniapps.realestate_ads import bp as realestate_bp, init_miniapp

    # Get core components
    job_store = app.job_store
    llm_client = app.llm_client
    tool_registry = app.tool_registry

    # Initialize artifact manager
    settings = app.config["SETTINGS"]
    artifact_manager = ArtifactManager(Path(settings.output.base_path))

    # Store in app config for routes
    app.config["JOB_STORE"] = job_store
    app.config["ARTIFACT_MANAGER"] = artifact_manager

    # Initialize and register realestate_ads mini app
    realestate_miniapp = init_miniapp(
        job_store, llm_client, tool_registry, artifact_manager
    )
    app.config["REALESTATE_ADS_MINIAPP"] = realestate_miniapp
    MINIAPPS["realestate_ads"] = realestate_miniapp

    # Register blueprint
    app.register_blueprint(realestate_bp)
