"""
AI Suite Backend Application Factory.

This module provides the Flask application factory pattern,
allowing for different configurations in development, testing, and production.
"""

from flask import Flask
from flask.json.provider import DefaultJSONProvider
import json
from datetime import datetime
from pathlib import Path

from config.settings import get_settings, Settings


class CustomJSONProvider(DefaultJSONProvider):
    """Custom JSON provider with datetime and Path serialization."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


def create_app(env: str = "development") -> Flask:
    """
    Create and configure the Flask application.

    Args:
        env: Environment name (development, testing, production)

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    app.json = CustomJSONProvider(app)

    # Load settings
    settings = get_settings()
    app.config["SETTINGS"] = settings
    app.config["DEBUG"] = settings.debug

    # Configure CORS for development
    if env == "development":
        _configure_cors(app)

    # Initialize core components
    _init_components(app)

    # Register blueprints
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _configure_cors(app: Flask) -> None:
    """Configure CORS for development."""

    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = (
            "GET, POST, PUT, DELETE, OPTIONS"
        )
        return response


def _init_components(app: Flask) -> None:
    """Initialize core application components."""
    from app.core.llm_client import LLMClient
    from app.core.job_runner import JobRunner
    from app.core.job_store import JobStore
    from app.core.tool_registry import ToolRegistry

    settings: Settings = app.config["SETTINGS"]

    # Initialize LLM client
    app.llm_client = LLMClient(settings.llm)

    # Initialize job store
    app.job_store = JobStore()

    # Initialize tool registry
    app.tool_registry = ToolRegistry(app.llm_client)

    # Initialize job runner
    app.job_runner = JobRunner(
        job_store=app.job_store,
        tool_registry=app.tool_registry,
        llm_client=app.llm_client,
        settings=settings.job,
    )


def _register_blueprints(app: Flask) -> None:
    """Register all application blueprints."""
    from app.routes.health import bp as health_bp
    from app.routes.api import bp as api_bp
    from app.routes.miniapps import bp as miniapps_bp
    from app.miniapps.registry import register_miniapps

    # Core routes
    app.register_blueprint(health_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(miniapps_bp)

    # Mini app routes
    register_miniapps(app)


def _register_error_handlers(app: Flask) -> None:
    """Register global error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        return {
            "status": "error",
            "error": "Bad Request",
            "details": str(error.description),
        }, 400

    @app.errorhandler(404)
    def not_found(error):
        return {
            "status": "error",
            "error": "Not Found",
            "details": str(error.description),
        }, 404

    @app.errorhandler(500)
    def internal_error(error):
        return {
            "status": "error",
            "error": "Internal Server Error",
            "details": "An unexpected error occurred",
        }, 500
