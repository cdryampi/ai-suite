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
    """Register all mini app blueprints."""
    # Mini apps will be registered here
    pass
