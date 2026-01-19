import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class ListingClassifier:
    """
    Service to classify real estate listings using LLM.
    Determines if a listing is from a private owner or an agency.
    """

    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self._prompt_template = self._load_prompt("classify_owner.txt")

    def _load_prompt(self, filename: str) -> str:
        """Load prompt template from file."""
        prompt_path = Path(__file__).parent / "prompts" / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    def classify_listing(self, listing_text: str) -> Dict[str, Any]:
        """
        Classify a listing text to determine if it's a private seller.

        Args:
            listing_text: The raw text content of the listing.

        Returns:
            Dict containing classification results.
            Default structure on error:
            {
                "is_private": False,
                "confidence": 0.0,
                "owner_name": None,
                "phone": None,
                "notes": "Error..."
            }
        """
        # Truncate text to avoid token limits (keep first 1500 + last 500)
        truncated_text = listing_text
        if len(listing_text) > 2000:
            truncated_text = listing_text[:1500] + "\n...\n" + listing_text[-500:]

        prompt = self._prompt_template.format(listing_text=truncated_text)

        response_content = ""
        try:
            response_content = self.llm_client.complete(
                prompt=prompt,
                max_tokens=500,
                temperature=0.1,  # Low temp for deterministic extraction
            )

            # Clean markdown code blocks if present
            cleaned_response = response_content.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]

            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]

            cleaned_response = cleaned_response.strip()

            data = json.loads(cleaned_response)

            # Normalize keys just in case
            return {
                "is_private": data.get("is_private", False),
                "confidence": data.get("confidence", 0.0),
                "owner_name": data.get("owner_name"),
                "phone": data.get("phone"),
                "notes": data.get("notes", ""),
            }

        except json.JSONDecodeError as e:
            logger.error(
                f"Failed to parse LLM response as JSON: {e}. Response: {response_content}"
            )
            return {
                "is_private": False,
                "confidence": 0.0,
                "owner_name": None,
                "phone": None,
                "notes": f"Failed to parse JSON response. Raw: {response_content[:100]}...",
            }
        except Exception as e:
            logger.error(f"Classification failed: {e}")
            return {
                "is_private": False,
                "confidence": 0.0,
                "owner_name": None,
                "phone": None,
                "notes": f"Error during classification: {str(e)}",
            }
