import os
import sys
import unittest
import json
from unittest.mock import MagicMock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.miniapps.market_scraper_privados.workflow import MarketScraperWorkflow
from app.miniapps.market_scraper_privados.providers.base import (
    ListingMetadata,
    RawListingData,
)


class TestMarketWorkflow(unittest.TestCase):
    def setUp(self):
        self.job_store = MagicMock()
        self.job_store.create.return_value = MagicMock(job_id="test_job_1", logs=[])

        self.llm_client = MagicMock()
        self.tool_registry = MagicMock()
        self.artifact_manager = MagicMock()
        self.artifact_manager.save_text.return_value = "/tmp/leads.csv"

        self.workflow = MarketScraperWorkflow(
            self.job_store, self.llm_client, self.tool_registry, self.artifact_manager
        )

    @patch("app.miniapps.market_scraper_privados.workflow.Database")
    @patch("app.miniapps.market_scraper_privados.workflow.IdealistaProvider")
    @patch("app.miniapps.market_scraper_privados.workflow.ListingClassifier")
    def test_run_success(self, MockClassifier, MockProvider, MockDatabase):
        # Mock DB
        mock_db = MockDatabase.return_value
        mock_db.exists_listing.return_value = False
        mock_db.get_pending_listings.return_value = [
            {
                "id": 1,
                "url": "http://test.com/1",
                "html_content": "<html>Description</html>",
                "parsed_data": '{"description": "desc"}',
            }
        ]

        # Mock Provider
        mock_provider = MockProvider.return_value
        mock_provider.name = "idealista"
        mock_provider.search.return_value = [
            ListingMetadata(external_id="1", url="http://test.com/1", title="Title")
        ]
        mock_provider.fetch_details.return_value = RawListingData(
            url="http://test.com/1",
            html_content="<html>Description</html>",
            parsed_data={"description": "desc"},
        )

        # Mock Classifier
        mock_classifier = MockClassifier.return_value
        mock_classifier.classify_listing.return_value = {
            "is_private": True,
            "confidence": 0.9,
            "owner_name": "Juan",
            "phone": "666",
            "notes": "Private",
        }

        # Run workflow
        result = self.workflow.run(json.dumps({"city": "TestCity"}))

        self.assertEqual(result.status, "ok")
        self.assertTrue(mock_db.save_raw_listing.called)
        self.assertTrue(mock_db.save_lead.called)
        self.assertTrue(self.artifact_manager.save_text.called)  # CSV export

        # Verify result stats
        print("Workflow Result:", result.result)
        self.assertEqual(result.result["scraped"], 1)
        self.assertEqual(result.result["private_found"], 1)


if __name__ == "__main__":
    unittest.main()
