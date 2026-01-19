"""
Scrape Tool - Web content extraction.

Fetches and extracts content from web pages.
Supports CSS selectors for targeted extraction.
"""

from typing import Optional
import logging

from app.tools.base import BaseTool, ToolResult


logger = logging.getLogger(__name__)


class ScrapeTool(BaseTool):
    """
    Scrape content from a web URL.

    Extracts text content, optionally filtered by CSS selector.
    """

    name = "scrape_url"
    description = "Scrape content from a web URL with optional CSS selector"

    input_schema = {
        "type": "object",
        "required": ["url"],
        "properties": {
            "url": {"type": "string", "description": "URL to scrape"},
            "selector": {
                "type": "string",
                "description": "CSS selector to filter content",
            },
            "timeout": {
                "type": "integer",
                "description": "Request timeout in seconds",
                "default": 30,
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "Extracted text content"},
            "title": {"type": "string", "description": "Page title"},
            "url": {"type": "string", "description": "Final URL (after redirects)"},
        },
    }

    def execute(self, inputs: dict) -> ToolResult:
        """
        Execute web scraping.

        Args:
            inputs: Scraping parameters

        Returns:
            ToolResult: Extracted content
        """
        try:
            import httpx
            from bs4 import BeautifulSoup
        except ImportError:
            return ToolResult(
                success=False,
                error="Scraping dependencies not installed (httpx, beautifulsoup4)",
            )

        url = inputs["url"]
        selector = inputs.get("selector")
        timeout = inputs.get("timeout", 30)

        try:
            # Fetch the page
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                response = client.get(
                    url,
                    headers={"User-Agent": "Mozilla/5.0 (compatible; AI-Suite/1.0)"},
                )
                response.raise_for_status()

            # Parse HTML
            soup = BeautifulSoup(response.text, "lxml")

            # Get title
            title = soup.title.string if soup.title else ""

            # Extract content
            if selector:
                elements = soup.select(selector)
                content = "\n\n".join(el.get_text(strip=True) for el in elements)
            else:
                # Remove scripts and styles
                for tag in soup(["script", "style", "nav", "footer", "header"]):
                    tag.decompose()
                content = soup.get_text(separator="\n", strip=True)

            return ToolResult(
                success=True,
                outputs={"content": content, "title": title, "url": str(response.url)},
            )

        except httpx.HTTPError as e:
            return ToolResult(success=False, error=f"HTTP error: {e}")
        except Exception as e:
            logger.error(f"Scrape failed: {e}")
            return ToolResult(success=False, error=str(e))
