"""
Test script for the Planner implementation (Windows-compatible).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.planner import Planner, ExecutionPlan, PlanStep
from app.core.llm_client import LLMClient
from app.core.tool_registry import ToolRegistry
from app.core.job_store import JobStore
from config.settings import get_settings


def test_planner_validation():
    """Test Planner validation logic."""
    print("\n" + "=" * 70)
    print("Testing Planner Validation")
    print("=" * 70)

    settings = get_settings()
    llm_client = LLMClient(settings.llm)
    tool_registry = ToolRegistry(llm_client)
    job_store = JobStore()
    planner = Planner(llm_client, tool_registry, job_store)

    # Test 1: Tool not in whitelist
    print("\n1. Testing tool whitelist validation...")
    plan = ExecutionPlan(
        goal="Test",
        steps=[
            PlanStep(
                step_number=1,
                tool_name="non_existent_tool",
                description="Test",
                inputs={},
                output_variable="result",
            )
        ],
    )

    try:
        planner._validate_plan(plan, allowed_tools=["scrape_url"])
        print("   [FAIL] Should have rejected tool not in whitelist")
        return False
    except ValueError as e:
        print(f"   [PASS] Correctly rejected: {e}")

    # Test 2: Tool not registered
    print("\n2. Testing unregistered tool validation...")
    plan = ExecutionPlan(
        goal="Test",
        steps=[
            PlanStep(
                step_number=1,
                tool_name="fake_tool",
                description="Test",
                inputs={},
                output_variable="result",
            )
        ],
    )

    try:
        planner._validate_plan(plan, allowed_tools=None)
        print("   [FAIL] Should have rejected unregistered tool")
        return False
    except ValueError as e:
        print(f"   [PASS] Correctly rejected: {e}")

    print("\n   All validation tests passed!")
    return True


def test_planner_simple_workflow():
    """Test Planner with a simple scrape workflow."""
    print("\n" + "=" * 70)
    print("Testing Planner Workflow Execution")
    print("=" * 70)

    # Initialize components
    print("\n1. Initializing components...")
    settings = get_settings()
    llm_client = LLMClient(settings.llm)
    tool_registry = ToolRegistry(llm_client)
    job_store = JobStore()

    print(f"   [OK] LLM Client initialized (provider: {settings.llm.provider})")
    print(
        f"   [OK] Tool Registry initialized ({len(tool_registry.list_tools())} tools)"
    )
    print(f"   [OK] Job Store initialized")

    # Initialize Planner
    planner = Planner(llm_client, tool_registry, job_store)
    print(f"   [OK] Planner initialized")

    # Create a manual plan (simulating what LLM would generate)
    print("\n2. Creating test plan...")
    plan = ExecutionPlan(
        goal="Test scraping a URL",
        context={"test_url": "https://httpbin.org/html"},
        steps=[
            PlanStep(
                step_number=1,
                tool_name="scrape_url",
                description="Scrape the test URL",
                inputs={"url": "$test_url", "timeout": 5},
                output_variable="scraped_content",
            )
        ],
    )

    print(f"   Created plan with {len(plan.steps)} step(s)")

    # Validate plan
    print("\n3. Validating plan...")
    try:
        planner._validate_plan(plan, allowed_tools=["scrape_url", "llm_generate"])
        print("   [PASS] Plan validation passed")
    except ValueError as e:
        print(f"   [FAIL] Plan validation failed: {e}")
        return False

    # Execute plan
    print("\n4. Executing plan...")
    plan.status = "running"

    for step in plan.steps:
        print(f"\n   Step {step.step_number}: {step.description}")
        print(f"   Tool: {step.tool_name}")
        print(f"   Inputs: {step.inputs}")

        try:
            step.status = "running"

            # Get tool
            tool = tool_registry.get_tool(step.tool_name)
            if not tool:
                raise ValueError(f"Tool not found: {step.tool_name}")

            # Resolve inputs
            resolved_inputs = planner._resolve_inputs(step.inputs, plan.context)
            print(f"   Resolved inputs: {resolved_inputs}")

            # Execute tool
            result = tool.execute(resolved_inputs)

            if not result.success:
                raise RuntimeError(f"Tool execution failed: {result.error}")

            # Store result
            plan.context[step.output_variable] = result.outputs
            step.result = result.outputs
            step.status = "completed"

            print(f"   [OK] Step completed")
            print(f"   Output stored in: {step.output_variable}")

            if isinstance(result.outputs, dict):
                print(f"   Result keys: {list(result.outputs.keys())}")

        except Exception as e:
            step.status = "failed"
            step.error = str(e)
            plan.status = "failed"
            print(f"   [FAIL] Step failed: {e}")
            break

    # Check final status
    if all(step.status == "completed" for step in plan.steps):
        plan.status = "completed"
        print("\n5. [SUCCESS] Plan execution completed!")
        return True
    else:
        print("\n5. [FAIL] Plan execution failed")
        return False


def main():
    """Run all tests."""
    print("\n=== PLANNER TEST SUITE ===\n")

    results = []

    # Run tests
    results.append(("Validation Tests", test_planner_validation()))
    results.append(("Simple Workflow Test", test_planner_simple_workflow()))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status}\t{name}")

    all_passed = all(result[1] for result in results)

    if all_passed:
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
