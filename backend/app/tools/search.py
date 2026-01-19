"""
Web search tool using DuckDuckGo.
"""

from typing import Any, Dict, List, Optional
from duckduckgo_search import DDGS

from .base import BaseTool, ToolResult


class SearchTool(BaseTool):
    """
    Tool for searching the web using DuckDuckGo.

    Returns a list of search results with title, URL, and snippet.
    """

    @property
    def name(self) -> str:
        return "search_web"

    @property
    def description(self) -> str:
        return "Search the web for a given query. Returns top results with titles and URLs."

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    @property
    def output_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "results": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "href": {"type": "string"},
                            "body": {"type": "string"},
                        },
                    },
                }
            },
        }

    def execute(self, inputs: Dict[str, Any]) -> ToolResult:
        """
        Execute the search.

        Args:
            inputs: Dictionary containing 'query' and optional 'max_results'

        Returns:
            ToolResult with search results
        """
        query = inputs.get("query")
        max_results = inputs.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="Missing required parameter: query")

        try:
            results = []
            with DDGS() as ddgs:
                # DDGS.text() returns a generator
                ddgs_gen = ddgs.text(query, max_results=max_results)
                if ddgs_gen:
                    for r in ddgs_gen:
                        results.append(
                            {
                                "title": r.get("title"),
                                "href": r.get("href"),
                                "body": r.get("body"),
                            }
                        )

            return ToolResult(success=True, outputs={"results": results})

        except Exception as e:
            return ToolResult(
                success=False, error=f"Search failed: {str(e)}", outputs={}
            )
