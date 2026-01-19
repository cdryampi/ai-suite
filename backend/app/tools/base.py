"""
Base Tool - Abstract base class for all tools.

All tools must inherit from BaseTool and implement the execute method.
Tools provide atomic capabilities that can be composed into workflows.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ToolResult:
    """
    Result from tool execution.

    Attributes:
        success: Whether execution succeeded
        outputs: Output data from the tool
        error: Error message if failed
        metadata: Additional metadata
    """

    success: bool
    outputs: dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseTool(ABC):
    """
    Abstract base class for workflow tools.

    All tools must define:
    - name: Unique identifier
    - description: Human-readable description
    - input_schema: JSON Schema for inputs
    - output_schema: JSON Schema for outputs
    - execute(): Implementation
    """

    # Tool metadata (must be overridden)
    name: str = "base_tool"
    description: str = "Base tool - do not use directly"

    # JSON Schema for inputs
    input_schema: dict = {"type": "object", "properties": {}}

    # JSON Schema for outputs
    output_schema: dict = {"type": "object", "properties": {}}

    def validate_inputs(self, inputs: dict) -> tuple[bool, Optional[str]]:
        """
        Validate inputs against the schema.

        Args:
            inputs: Input data to validate

        Returns:
            tuple: (is_valid, error_message)
        """
        # Check required fields
        required = self.input_schema.get("required", [])
        for field in required:
            if field not in inputs:
                return False, f"Missing required field: {field}"

        # Basic type checking
        properties = self.input_schema.get("properties", {})
        for field, value in inputs.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type and not self._check_type(value, expected_type):
                    return False, f"Invalid type for {field}: expected {expected_type}"

        return True, None

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON Schema type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        expected = type_map.get(expected_type)
        if expected:
            return isinstance(value, expected)
        return True

    @abstractmethod
    def execute(self, inputs: dict) -> ToolResult:
        """
        Execute the tool.

        Args:
            inputs: Validated input parameters

        Returns:
            ToolResult: Execution result
        """
        pass

    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"
