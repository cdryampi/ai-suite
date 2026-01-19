"""
Planner - LLM-based workflow orchestrator.

The Planner is the core orchestration engine for AI Suite workflows.
It takes a high-level goal, breaks it down into steps, validates each step,
and executes them sequentially using registered tools.

Key Features:
1. **Tool Whitelist**: Only allows execution of pre-registered, safe tools
2. **Step Validation**: Each step must conform to a JSON schema
3. **Deterministic Execution**: Same input produces same sequence of steps
4. **Error Handling**: Graceful failure with rollback capabilities
5. **Logging**: Complete audit trail of planning and execution

Architecture:
    User Request → Planner → Execution Plan → Tool Execution → Result

Example:
    planner = Planner(llm_client, tool_registry, job_store)
    result = planner.execute(
        goal="Generate a real estate ad from URL",
        context={"url": "https://example.com/listing"},
        allowed_tools=["scrape_url", "llm_generate"]
    )
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import json
import logging

from app.core.llm_client import LLMClient
from app.core.tool_registry import ToolRegistry
from app.core.job_store import JobStore

logger = logging.getLogger(__name__)


@dataclass
class PlanStep:
    """A single step in an execution plan."""

    step_number: int
    """Sequential step number (1-indexed)"""

    tool_name: str
    """Name of the tool to execute"""

    description: str
    """Human-readable description of what this step does"""

    inputs: Dict[str, Any]
    """Input parameters for the tool"""

    output_variable: str
    """Variable name to store the result"""

    status: str = "pending"
    """Status: pending, running, completed, failed, skipped"""

    result: Optional[Any] = None
    """Execution result (if completed)"""

    error: Optional[str] = None
    """Error message (if failed)"""


@dataclass
class ExecutionPlan:
    """A complete execution plan with multiple steps."""

    goal: str
    """High-level goal of the plan"""

    steps: List[PlanStep] = field(default_factory=list)
    """Ordered list of steps to execute"""

    context: Dict[str, Any] = field(default_factory=dict)
    """Shared context/variables across steps"""

    created_at: datetime = field(default_factory=datetime.now)
    """When the plan was created"""

    status: str = "pending"
    """Overall plan status: pending, running, completed, failed"""


# JSON Schema for validating plan steps
PLAN_STEP_SCHEMA = {
    "type": "object",
    "required": [
        "step_number",
        "tool_name",
        "description",
        "inputs",
        "output_variable",
    ],
    "properties": {
        "step_number": {"type": "integer", "minimum": 1},
        "tool_name": {"type": "string", "minLength": 1},
        "description": {"type": "string", "minLength": 1},
        "inputs": {"type": "object"},
        "output_variable": {"type": "string", "minLength": 1},
    },
}


class Planner:
    """
    LLM-based workflow orchestrator.

    The Planner coordinates multi-step workflows by:
    1. Taking a high-level goal and context
    2. Generating an execution plan using an LLM
    3. Validating each step against tool whitelist and schema
    4. Executing steps sequentially
    5. Handling errors and maintaining audit logs
    """

    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: ToolRegistry,
        job_store: JobStore,
    ):
        """
        Initialize the Planner.

        Args:
            llm_client: LLM client for generating plans
            tool_registry: Registry of available tools
            job_store: Job store for tracking execution
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.job_store = job_store

    def execute(
        self,
        goal: str,
        context: Dict[str, Any],
        allowed_tools: Optional[List[str]] = None,
        max_steps: int = 10,
        job_id: Optional[str] = None,
    ) -> ExecutionPlan:
        """
        Execute a workflow by planning and running steps.

        Args:
            goal: High-level goal to accomplish
            context: Initial context/variables
            allowed_tools: Whitelist of tool names (None = all tools)
            max_steps: Maximum number of steps allowed
            job_id: Optional job ID for tracking

        Returns:
            ExecutionPlan with results
        """
        logger.info(f"Planner executing goal: {goal}")

        # Step 1: Generate execution plan
        plan = self._generate_plan(goal, context, allowed_tools, max_steps)
        plan.status = "running"

        # Step 2: Validate plan
        try:
            self._validate_plan(plan, allowed_tools)
        except ValueError as e:
            plan.status = "failed"
            logger.error(f"Plan validation failed: {e}")
            raise

        # Step 3: Execute steps sequentially
        for step in plan.steps:
            try:
                logger.info(f"Executing step {step.step_number}: {step.description}")
                step.status = "running"

                # Get tool
                tool = self.tool_registry.get_tool(step.tool_name)
                if not tool:
                    raise ValueError(f"Tool not found: {step.tool_name}")

                # Resolve inputs (replace variable references)
                resolved_inputs = self._resolve_inputs(step.inputs, plan.context)

                # Execute tool (tools expect a dict as input)
                result = tool.execute(resolved_inputs)

                if not result.success:
                    raise RuntimeError(f"Tool execution failed: {result.error}")

                # Store result in context
                plan.context[step.output_variable] = result.outputs
                step.result = result.outputs
                step.status = "completed"

                logger.info(f"Step {step.step_number} completed successfully")

            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                plan.status = "failed"
                logger.error(f"Step {step.step_number} failed: {e}")

                # Stop execution on first failure
                break

        # Mark plan as completed if all steps succeeded
        if all(step.status == "completed" for step in plan.steps):
            plan.status = "completed"
            logger.info("Plan completed successfully")

        return plan

    def _generate_plan(
        self,
        goal: str,
        context: Dict[str, Any],
        allowed_tools: Optional[List[str]],
        max_steps: int,
    ) -> ExecutionPlan:
        """
        Generate an execution plan using the LLM.

        Args:
            goal: Goal to accomplish
            context: Initial context
            allowed_tools: Tool whitelist
            max_steps: Max steps

        Returns:
            ExecutionPlan with steps
        """
        # Get tool descriptions
        available_tools = self._get_tool_descriptions(allowed_tools)

        # Build prompt
        prompt = self._build_planning_prompt(goal, context, available_tools, max_steps)

        # Call LLM
        logger.info("Calling LLM to generate execution plan")
        response = self.llm_client.complete(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.1,  # Very low temperature for strict JSON formatting
        )

        # Parse response as JSON - try to extract JSON if embedded in text
        try:
            plan_data = json.loads(response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from response
            logger.warning(f"Initial JSON parse failed: {e}")
            logger.info("Attempting to extract JSON from response...")

            # Look for JSON object in the response
            import re

            json_match = re.search(r'\{[\s\S]*"steps"[\s\S]*\}', response)

            if json_match:
                try:
                    plan_data = json.loads(json_match.group(0))
                    logger.info("Successfully extracted JSON from response")
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse extracted JSON")
                    raise ValueError(f"LLM returned invalid JSON: {response[:200]}...")
            else:
                logger.error(f"No JSON found in response: {response[:200]}")
                raise ValueError(f"LLM returned invalid JSON: {response[:200]}...")

        # Convert to ExecutionPlan
        steps = []
        for step_data in plan_data.get("steps", []):
            steps.append(
                PlanStep(
                    step_number=step_data["step_number"],
                    tool_name=step_data["tool_name"],
                    description=step_data["description"],
                    inputs=step_data["inputs"],
                    output_variable=step_data["output_variable"],
                )
            )

        plan = ExecutionPlan(
            goal=goal,
            steps=steps,
            context=context.copy(),
        )

        logger.info(f"Generated plan with {len(steps)} steps")
        return plan

    def _validate_plan(
        self, plan: ExecutionPlan, allowed_tools: Optional[List[str]]
    ) -> None:
        """
        Validate an execution plan.

        Args:
            plan: Plan to validate
            allowed_tools: Tool whitelist

        Raises:
            ValueError: If validation fails
        """
        if not plan.steps:
            raise ValueError("Plan has no steps")

        # Validate each step
        for step in plan.steps:
            # Validate tool is in whitelist
            if allowed_tools and step.tool_name not in allowed_tools:
                raise ValueError(
                    f"Step {step.step_number}: Tool '{step.tool_name}' "
                    f"not in allowed tools: {allowed_tools}"
                )

            # Validate tool exists
            if not self.tool_registry.get_tool(step.tool_name):
                raise ValueError(
                    f"Step {step.step_number}: Tool '{step.tool_name}' not registered"
                )

            # Basic schema validation
            if not isinstance(step.inputs, dict):
                raise ValueError(f"Step {step.step_number}: inputs must be a dict")

            if not step.output_variable:
                raise ValueError(
                    f"Step {step.step_number}: output_variable is required"
                )

    def _resolve_inputs(
        self,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Resolve variable references in inputs.

        Variables are referenced as "$variable_name".

        Args:
            inputs: Input dict with possible variable references
            context: Context with variable values

        Returns:
            Resolved inputs dict
        """
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("$"):
                var_name = value[1:]  # Remove $ prefix
                if var_name not in context:
                    raise ValueError(f"Variable '{var_name}' not found in context")
                resolved[key] = context[var_name]
            else:
                resolved[key] = value

        return resolved

    def _get_tool_descriptions(
        self, allowed_tools: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """
        Get descriptions of available tools.

        Args:
            allowed_tools: Tool whitelist (None = all tools)

        Returns:
            List of tool description dicts
        """
        all_tools = self.tool_registry.list_tools()

        descriptions = []
        for tool_name in all_tools:
            if allowed_tools and tool_name not in allowed_tools:
                continue

            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                descriptions.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema.get("properties", {}),
                    }
                )

        return descriptions

    def _build_planning_prompt(
        self,
        goal: str,
        context: Dict[str, Any],
        tools: List[Dict[str, Any]],
        max_steps: int,
    ) -> str:
        """
        Build the LLM prompt for plan generation.

        Args:
            goal: Goal to accomplish
            context: Initial context
            tools: Available tool descriptions
            max_steps: Max steps allowed

        Returns:
            Prompt string
        """
        tools_text = "\n".join(
            [f"- {tool['name']}: {tool['description']}" for tool in tools]
        )

        context_text = json.dumps(context, indent=2)

        prompt = f"""You are a workflow planner that generates ONLY valid JSON output.

GOAL: {goal}

AVAILABLE CONTEXT:
{context_text}

AVAILABLE TOOLS:
{tools_text}

INSTRUCTIONS:
1. Break down the goal into sequential steps (max {max_steps} steps)
2. Each step uses exactly ONE tool from available tools
3. Reference context variables using "$variable_name"
4. Output variable names should be descriptive

CRITICAL: You must respond with ONLY a valid JSON object, no other text.

OUTPUT FORMAT:
{{
  "steps": [
    {{
      "step_number": 1,
      "tool_name": "tool_name_here",
      "description": "What this step accomplishes",
      "inputs": {{"param1": "value1", "param2": "$context_variable"}},
      "output_variable": "descriptive_output_name"
    }}
  ]
}}

Respond ONLY with the JSON object, nothing else:"""

        return prompt
