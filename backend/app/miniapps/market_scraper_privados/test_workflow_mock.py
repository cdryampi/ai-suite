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
        # Mock JobStore
        self.job_store = MagicMock()

        # Mock Job
        self.job_mock = MagicMock()
        self.job_mock.job_id = "test_job_1"
        self.job_mock.logs = []
        self.job_mock.result = {}  # Initialize result

        # When complete is called, update result
        def side_effect_complete(result):
            self.job_mock.result = result

        self.job_mock.complete.side_effect = side_effect_complete

        self.job_store.create.return_value = self.job_mock

        self.llm_client = MagicMock()
        self.tool_registry = MagicMock()
        self.artifact_manager = MagicMock()
        self.artifact_manager.save_text.return_value = "/tmp/leads.csv"

        self.workflow = MarketScraperWorkflow(
            self.job_store, self.llm_client, self.tool_registry, self.artifact_manager
        )

    @patch("app.miniapps.market_scraper_privados.workflow.Database")
    @patch("app.miniapps.market_scraper_privados.workflow.FotocasaProvider")
    @patch("app.miniapps.market_scraper_privados.workflow.IdealistaProvider")
    @patch("app.miniapps.market_scraper_privados.workflow.ListingClassifier")
    def test_run_success(
        self, MockClassifier, MockIdealista, MockFotocasa, MockDatabase
    ):
        # Mock DB
        mock_db = MockDatabase.return_value
        mock_db.exists_listing.return_value = False
        # Return one pending listing to classify (simulating one was new)
        mock_db.get_pending_listings.return_value = [
            {
                "id": 1,
                "url": "http://test.com/1",
                "html_content": "<html>Description</html>",
                "parsed_data": '{"description": "desc"}',
            }
        ]

        # Mock Idealista
        mock_idealista = MockIdealista.return_value
        mock_idealista.name = "idealista"
        mock_idealista.search.return_value = [
            ListingMetadata(
                external_id="1", url="http://idealista.com/1", title="Title"
            )
        ]
        mock_idealista.fetch_details.return_value = RawListingData(
            url="http://idealista.com/1",
            html_content="<html>Description</html>",
            parsed_data={"description": "desc"},
        )

        # Mock Fotocasa
        mock_fotocasa = MockFotocasa.return_value
        mock_fotocasa.name = "fotocasa"
        mock_fotocasa.search.return_value = [
            ListingMetadata(
                external_id="2", url="http://fotocasa.es/2", title="Title 2"
            )
        ]
        mock_fotocasa.fetch_details.return_value = RawListingData(
            url="http://fotocasa.es/2",
            html_content="<html>Description 2</html>",
            parsed_data={"description": "desc 2"},
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
        # 1 from Idealista + 1 from Fotocasa = 2 scraped
        print("Workflow Result:", result.result)
        self.assertEqual(result.result["scraped"], 2)
        # We mocked get_pending_listings to return 1 item, so 1 classified
        self.assertEqual(result.result["private_found"], 1)


if __name__ == "__main__":
    unittest.main()
