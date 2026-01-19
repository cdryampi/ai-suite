"""Quick test of core implementations"""
import sys
sys.path.insert(0, '.')

print("Testing core modules...")

# Test imports
from app.core.llm_client import LLMClient, Message
from app.core.job_store import JobStore, Job, JobStatus
from app.core.job_runner import JobRunner
from app.core.tool_registry import ToolRegistry
from app.core.artifacts import ArtifactManager
from app.tools.base import BaseTool, ToolResult

print("[OK] All core modules imported successfully")

# Test job store
from config.settings import get_settings
settings = get_settings()

job_store = JobStore()
job = job_store.create("test_app", {"input": "test"})
assert job.job_id.startswith("job_")
print(f"[OK] Job store: created job {job.job_id}")

# Test artifact manager
artifact_mgr = ArtifactManager()
print(f"[OK] Artifact manager initialized at {artifact_mgr.base_path}")

# Test tool registry
llm_client = LLMClient(settings.llm)
tool_registry = ToolRegistry(llm_client)
print(f"[OK] Tool registry initialized with {len(tool_registry.list_tools())} tools")

print("\n=== All core components working ===")
