"""
LLM Generate Tool - Text generation using LLM.

This tool wraps the LLM client to provide text generation
as a workflow step.
"""

from pathlib import Path
from typing import Optional

from app.tools.base import BaseTool, ToolResult
from app.core.llm_client import LLMClient, Message


class LLMGenerateTool(BaseTool):
    """
    Generate text using the LLM.

    Can use a prompt template file or a direct prompt string.
    Supports context injection via Jinja2-style templating.
    """

    name = "llm_generate"
    description = "Generate text using the LLM with an optional prompt template"

    input_schema = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "Direct prompt text (alternative to template)",
            },
            "prompt_template": {
                "type": "string",
                "description": "Path to prompt template file",
            },
            "context": {
                "type": "string",
                "description": "Context to inject into the prompt",
            },
            "system_prompt": {
                "type": "string",
                "description": "Optional system prompt",
            },
            "max_tokens": {
                "type": "integer",
                "description": "Maximum tokens to generate",
                "default": 1000,
            },
            "temperature": {
                "type": "number",
                "description": "Sampling temperature (0-1)",
                "default": 0.7,
            },
        },
    }

    output_schema = {
        "type": "object",
        "properties": {
            "generated": {"type": "string", "description": "Generated text"}
        },
    }

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the LLM generate tool.

        Args:
            llm_client: LLM client instance
        """
        self.llm = llm_client

    def execute(self, inputs: dict) -> ToolResult:
        """
        Execute LLM generation.

        Args:
            inputs: Generation parameters

        Returns:
            ToolResult: Generated text
        """
        try:
            # Get the prompt
            prompt = self._build_prompt(inputs)

            if not prompt:
                return ToolResult(
                    success=False,
                    error="No prompt provided (need 'prompt' or 'prompt_template')",
                )

            # Get generation parameters
            max_tokens = inputs.get("max_tokens", 1000)
            temperature = inputs.get("temperature", 0.7)
            system_prompt = inputs.get("system_prompt")

            # Generate
            if system_prompt:
                messages = [
                    Message(role="system", content=system_prompt),
                    Message(role="user", content=prompt),
                ]
                result = self.llm.chat(
                    messages, max_tokens=max_tokens, temperature=temperature
                )
            else:
                result = self.llm.complete(
                    prompt, max_tokens=max_tokens, temperature=temperature
                )

            return ToolResult(success=True, outputs={"generated": result})

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def _build_prompt(self, inputs: dict) -> Optional[str]:
        """Build the prompt from inputs."""
        prompt = inputs.get("prompt")
        template_path = inputs.get("prompt_template")
        context = inputs.get("context", "")

        if template_path:
            # Load template file
            path = Path(template_path)
            if path.exists():
                prompt = path.read_text(encoding="utf-8")
            else:
                # Try relative to mini app prompts dir
                # This will be resolved by the workflow
                prompt = template_path

        if prompt and context:
            # Simple template substitution
            prompt = prompt.replace("{{ context }}", context)
            prompt = prompt.replace("{{context}}", context)

        return prompt
