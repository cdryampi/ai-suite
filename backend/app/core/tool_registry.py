"""
Tool Registry - Central registry for available tools.

All tools must be registered here to be available for use
by workflows and the Planner.
"""

from typing import Optional

from app.core.llm_client import LLMClient
from app.tools.base import BaseTool


class ToolRegistry:
    """
    Central registry for workflow tools.

    Maintains a mapping of tool names to tool instances,
    providing discovery and access for the Planner and workflows.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the tool registry.

        Args:
            llm_client: LLM client for tools that need it
        """
        self.llm_client = llm_client
        self._tools: dict[str, BaseTool] = {}

        # Register built-in tools
        self._register_builtin_tools()

    def _register_builtin_tools(self) -> None:
        """Register the default set of tools."""
        try:
            from app.tools.llm_tool import LLMGenerateTool
            from app.tools.scrape import ScrapeTool
            from app.tools.image_gen import ImageGenerateTool
            from app.tools.video_gen import VideoGenerateTool

            self.register(LLMGenerateTool(self.llm_client))
            self.register(ScrapeTool())
            self.register(ImageGenerateTool())
            self.register(VideoGenerateTool())
        except ImportError as e:
            # Tools not implemented yet - skip registration
            pass

    def register(self, tool: BaseTool) -> None:
        """
        Register a tool.

        Args:
            tool: The tool instance to register
        """
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.

        Args:
            name: The tool name

        Returns:
            BaseTool or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> list[str]:
        """
        List all registered tool names.

        Returns:
            list[str]: Tool names
        """
        return list(self._tools.keys())

    def get_tool_info(self) -> list[dict]:
        """
        Get information about all registered tools.

        Returns:
            list[dict]: Tool metadata
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
            }
            for tool in self._tools.values()
        ]
