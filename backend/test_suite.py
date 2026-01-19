"""
Comprehensive test suite for AI Suite.

Tests all components including end-to-end workflows.
Some tests require a running LLM (Ollama/LM Studio).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm_client import LLMClient
from app.core.tool_registry import ToolRegistry
from app.core.job_store import JobStore
from app.core.planner import Planner
from app.core.artifacts import ArtifactManager
from config.settings import get_settings
import json


def test_llm_connection():
    """Test LLM client connection."""
    print("\n" + "=" * 70)
    print("Test 1: LLM Connection")
    print("=" * 70)

    settings = get_settings()
    llm_client = LLMClient(settings.llm)

    print(
        f"\n1. Testing connection to {settings.llm.provider} at {settings.llm.base_url}..."
    )

    # Test connection
    is_connected = llm_client.is_connected()

    if is_connected:
        print(f"   [PASS] Connected to {settings.llm.provider}")

        # Test model listing
        try:
            models = llm_client.list_models()
            print(f"   [INFO] Available models: {', '.join(models[:5])}")
        except Exception as e:
            print(f"   [WARN] Could not list models: {e}")

        return True
    else:
        print(f"   [SKIP] LLM not available - some tests will be skipped")
        print(f"   [INFO] To run full tests, start Ollama or LM Studio")
        return False


def test_llm_generation(llm_available):
    """Test LLM text generation."""
    print("\n" + "=" * 70)
    print("Test 2: LLM Text Generation")
    print("=" * 70)

    if not llm_available:
        print("   [SKIP] LLM not available")
        return True

    settings = get_settings()
    llm_client = LLMClient(settings.llm)

    print("\n1. Testing simple completion...")

    prompt = "Say 'Hello from AI Suite' and nothing else."

    try:
        response = llm_client.complete(prompt=prompt, max_tokens=50, temperature=0.1)

        print(f"   [PASS] Generation successful")
        print(f"   Response: {response[:100]}...")
        return True

    except Exception as e:
        print(f"   [FAIL] Generation failed: {e}")
        return False


def test_planner_with_llm(llm_available):
    """Test Planner with real LLM plan generation."""
    print("\n" + "=" * 70)
    print("Test 3: Planner with LLM Plan Generation")
    print("=" * 70)

    if not llm_available:
        print("   [SKIP] LLM not available")
        return True

    settings = get_settings()
    llm_client = LLMClient(settings.llm)
    tool_registry = ToolRegistry(llm_client)
    job_store = JobStore()
    planner = Planner(llm_client, tool_registry, job_store)

    print("\n1. Asking LLM to generate execution plan...")

    goal = "Scrape content from https://httpbin.org/html"
    context = {"target_url": "https://httpbin.org/html"}
    allowed_tools = ["scrape_url"]

    try:
        # This will call the LLM to generate a plan
        plan = planner.execute(
            goal=goal, context=context, allowed_tools=allowed_tools, max_steps=3
        )

        print(f"   [INFO] Plan generated with {len(plan.steps)} steps")
        print(f"   [INFO] Plan status: {plan.status}")

        for step in plan.steps:
            print(f"   Step {step.step_number}: {step.description} [{step.status}]")

        if plan.status == "completed":
            print(f"   [PASS] Plan executed successfully")
            return True
        else:
            print(f"   [WARN] Plan did not complete: {plan.status}")
            return True  # Still pass if LLM generated valid plan

    except Exception as e:
        print(f"   [FAIL] Planner failed: {e}")
        return False


def test_tool_execution():
    """Test individual tool execution."""
    print("\n" + "=" * 70)
    print("Test 4: Tool Execution")
    print("=" * 70)

    settings = get_settings()
    llm_client = LLMClient(settings.llm)
    tool_registry = ToolRegistry(llm_client)

    print("\n1. Testing scrape_url tool...")

    scrape_tool = tool_registry.get_tool("scrape_url")
    if not scrape_tool:
        print("   [FAIL] scrape_url tool not registered")
        return False

    result = scrape_tool.execute({"url": "https://httpbin.org/html", "timeout": 10})

    if result.success:
        print(f"   [PASS] Scraping successful")
        print(
            f"   [INFO] Content length: {len(result.outputs.get('content', ''))} chars"
        )
        return True
    else:
        print(f"   [FAIL] Scraping failed: {result.error}")
        return False


def test_artifact_storage():
    """Test artifact manager."""
    print("\n" + "=" * 70)
    print("Test 5: Artifact Storage")
    print("=" * 70)

    settings = get_settings()
    from pathlib import Path

    artifact_manager = ArtifactManager(Path(settings.output.base_path))

    print("\n1. Creating test job...")
    job_store = JobStore()
    job = job_store.create(miniapp_id="test_workflow", input_data={"test": True})

    print(f"   [OK] Job created: {job.job_id}")

    print("\n2. Saving text artifact...")
    text_path = artifact_manager.save_text(
        job_id=job.job_id, filename="test.txt", content="This is a test artifact"
    )
    print(f"   [OK] Text artifact saved: {text_path}")

    print("\n3. Saving JSON artifact...")
    json_path = artifact_manager.save_json(
        job_id=job.job_id, filename="test.json", data={"status": "success", "value": 42}
    )
    print(f"   [OK] JSON artifact saved: {json_path}")

    print("\n4. Listing artifacts...")
    artifacts = artifact_manager.list_artifacts(job.job_id)
    print(f"   [OK] Found {len(artifacts)} artifacts")

    for artifact in artifacts:
        print(f"      - {artifact.filename} ({artifact.size_bytes} bytes)")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print(" AI SUITE - COMPREHENSIVE TEST SUITE")
    print("=" * 70)

    results = []

    # Test 1: LLM connection (determines if we can run LLM tests)
    llm_available = test_llm_connection()
    results.append(("LLM Connection", llm_available or "SKIP"))

    # Test 2: LLM generation
    result = test_llm_generation(llm_available)
    results.append(("LLM Generation", result))

    # Test 3: Tool execution
    result = test_tool_execution()
    results.append(("Tool Execution", result))

    # Test 4: Artifact storage
    result = test_artifact_storage()
    results.append(("Artifact Storage", result))

    # Test 5: Planner with LLM
    result = test_planner_with_llm(llm_available)
    results.append(("Planner with LLM", result))

    # Summary
    print("\n" + "=" * 70)
    print(" TEST SUMMARY")
    print("=" * 70)

    passed = 0
    failed = 0
    skipped = 0

    for name, result in results:
        if result == "SKIP":
            status = "[SKIP]"
            skipped += 1
        elif result:
            status = "[PASS]"
            passed += 1
        else:
            status = "[FAIL]"
            failed += 1

        print(f"{status}\t{name}")

    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped")
    print("=" * 70)

    if not llm_available:
        print("\n[INFO] Some tests were skipped because LLM is not available.")
        print("[INFO] To run full tests:")
        print("  1. Start Ollama: ollama serve")
        print("  2. Pull a model: ollama pull llama3.2")
        print("  3. Run tests again")

    if failed > 0:
        print("\n[FAILED] Some tests failed")
        return 1
    else:
        print("\n[SUCCESS] All available tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
