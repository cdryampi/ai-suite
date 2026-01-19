import os
import sys
import unittest
from unittest.mock import MagicMock
import json

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.miniapps.market_scraper_privados.classifier import ListingClassifier


class TestClassifier(unittest.TestCase):
    def setUp(self):
        self.mock_llm = MagicMock()
        self.classifier = ListingClassifier(self.mock_llm)

    def test_classify_private(self):
        # Mock LLM response with new structure
        response_data = {
            "is_private": True,
            "confidence": 0.9,
            "owner_name": "Juan",
            "phone": "600123456",
            "notes": "Says 'Soy particular'",
        }
        self.mock_llm.complete.return_value = json.dumps(response_data)

        text = "Se vende piso. Soy particular. Abstenerse agencias."
        result = self.classifier.classify_listing(text)

        self.assertTrue(result["is_private"])
        self.assertEqual(result["confidence"], 0.9)
        self.assertEqual(result["owner_name"], "Juan")
        self.assertEqual(result["phone"], "600123456")

    def test_classify_agency(self):
        # Mock LLM response
        response_data = {
            "is_private": False,
            "confidence": 0.95,
            "owner_name": None,
            "phone": None,
            "notes": "Mentions 'Honorarios de agencia'",
        }
        self.mock_llm.complete.return_value = json.dumps(response_data)

        text = "Piso en venta. Honorarios de agencia no incluidos."
        result = self.classifier.classify_listing(text)

        self.assertFalse(result["is_private"])

    def test_handle_invalid_json(self):
        self.mock_llm.complete.return_value = "Not a JSON"

        text = "..."
        result = self.classifier.classify_listing(text)

        self.assertFalse(result["is_private"])
        self.assertEqual(result["confidence"], 0.0)
        self.assertIn("Failed to parse", result["notes"])


if __name__ == "__main__":
    unittest.main()
