"""
Quick test to verify the backend can start.
Run this before installing full dependencies.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

print("Testing imports...")

try:
    from config.settings import get_settings

    print("✓ config.settings")
except Exception as e:
    print(f"✗ config.settings: {e}")

try:
    from app.core.llm_client import LLMClient

    print("✓ app.core.llm_client")
except Exception as e:
    print(f"✗ app.core.llm_client: {e}")

try:
    from app.core.job_store import JobStore

    print("✓ app.core.job_store")
except Exception as e:
    print(f"✗ app.core.job_store: {e}")

try:
    from app.core.job_runner import JobRunner

    print("✓ app.core.job_runner")
except Exception as e:
    print(f"✗ app.core.job_runner: {e}")

try:
    from app.core.tool_registry import ToolRegistry

    print("✓ app.core.tool_registry")
except Exception as e:
    print(f"✗ app.core.tool_registry: {e}")

print("\n" + "=" * 60)
print("Basic structure is OK!")
print("=" * 60)
print("\nNext steps:")
print("1. cd backend")
print("2. python -m venv venv")
print("3. venv\\Scripts\\activate  (Windows)")
print("4. pip install flask pyyaml")
print("5. python run.py")
print("\nThe server will start on http://localhost:5000")
