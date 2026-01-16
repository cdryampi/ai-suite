"""
Tool Registry stub - minimal implementation.
"""


class ToolRegistry:
    """Stub tool registry."""

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self._tools = {}

    def register(self, tool):
        pass

    def get_tool(self, name):
        return None
