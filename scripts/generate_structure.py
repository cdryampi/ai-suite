#!/usr/bin/env python3
"""
Script to generate all remaining AI Suite project files.
This creates the complete project structure with all necessary files.
"""

import os
from pathlib import Path

# Base path
BASE = Path(__file__).parent.parent

# File contents dictionary - only critical files for now
FILES = {
    # Backend config
    "backend/config/__init__.py": '''"""
Configuration management for AI Suite backend.
"""
from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
''',
    # Core modules __init__ files
    "backend/app/core/__init__.py": '"""Core application components."""',
    "backend/app/routes/__init__.py": '"""API Routes package."""',
    "backend/app/tools/__init__.py": '"""Tools package."""',
    "backend/app/miniapps/__init__.py": '"""Mini Apps package."""',
    "backend/app/utils/__init__.py": '"""Utility modules."""',
    "backend/tests/__init__.py": '"""Test suite."""',
    # Empty prompt files for realestate_ads
    "backend/app/miniapps/realestate_ads/__init__.py": '''"""
Real Estate Ads Mini App
"""
from .workflow import RealEstateAdsWorkflow

__all__ = ["RealEstateAdsWorkflow"]
''',
}


def create_files():
    """Create all project files."""
    for filepath, content in FILES.items():
        full_path = BASE / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        print(f"Creating: {filepath}")
        full_path.write_text(content, encoding="utf-8")

    print(f"\n✓ Created {len(FILES)} files")


if __name__ == "__main__":
    create_files()
    print("\nNext steps:")
    print("1. Run the full generator script (will be created)")
    print(
        "2. Install backend dependencies: cd backend && python -m venv venv && venv\\Scripts\\activate && pip install -r requirements.txt"
    )
    print("3. Install frontend dependencies: cd frontend && npm install")
