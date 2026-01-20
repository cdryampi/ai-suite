import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable

from app.miniapps.base import BaseMiniApp, MiniAppMetadata, MiniAppResult
from .db import Database
from .classifier import ListingClassifier
from .exporter import LeadExporter
from .providers.idealista import IdealistaProvider
from .providers.fotocasa import FotocasaProvider
from .providers.habitaclia import HabitacliaProvider
from .providers.milanuncios import MilanunciosProvider
from .providers.pisos import PisosProvider
from .providers.wallapop import WallapopProvider

logger = logging.getLogger(__name__)


class MarketScraperWorkflow(BaseMiniApp):
    """
    Workflow for scraping, classifying, and exporting private real estate leads.
    """

    def get_metadata(self) -> MiniAppMetadata:
        return MiniAppMetadata(
            id="market_scraper_privados",
            name="Private Market Scraper",
            description="Scrapes and identifies private real estate listings.",
            version="1.3.0",
            author="Sttil Team",
            tags=["real-estate", "scraper", "lead-gen"],
            variants={
                1: "Default - All 6 Providers (Idealista, Fotocasa, Habitaclia, Milanuncios, Pisos, Wallapop)"
            },
        )

    def execute(self, job: Any, on_log: Callable[[str], None]) -> Dict[str, Any]:
        """
        Core execution logic designed for JobRunner.

        Args:
            job: Job object (containing input_data)
            on_log: Callback to send log messages

        Returns:
            Dict containing the result
        """
        try:
            input_data = job.input_data or {}
            city = input_data.get("city", "madrid")
            max_items = int(input_data.get("max_items", 5))

            on_log(f"Starting Market Scraper for {city} (Max: {max_items})")

            # 1. Initialize DB
            db = Database()

            # 2. Scraping (Multi-provider)
            on_log("Starting scraping phase...")

            providers = [
                IdealistaProvider(),
                FotocasaProvider(),
                HabitacliaProvider(),
                MilanunciosProvider(),
                PisosProvider(),
                WallapopProvider(),
            ]

            total_new_count = 0

            for provider in providers:
                on_log(f"Running provider: {provider.name}...")
                try:
                    found_listings = provider.search(city, max_items)
                    on_log(f"Found {len(found_listings)} items on {provider.name}")

                    for meta in found_listings:
                        if not db.exists_listing(meta.url):
                            # Fetch details
                            details = provider.fetch_details(meta.url)
                            if details:
                                db.save_raw_listing(
                                    url=details.url,
                                    source=provider.name,
                                    external_id=meta.external_id,
                                    html_content=details.html_content,
                                    parsed_data=details.parsed_data,
                                )
                                total_new_count += 1
                except Exception as e:
                    logger.error(f"Provider {provider.name} failed: {e}")
                    on_log(f"Error running {provider.name}: {e}")

            on_log(f"Scraping finished. Total new listings: {total_new_count}")

            # 3. Classification
            on_log("Starting classification phase...")
            classifier = ListingClassifier(self.llm_client)
            pending = db.get_pending_listings()

            classified_count = 0
            private_count = 0

            for item in pending:
                # We can log progress here per item if needed
                # on_log(f"Classifying {item['url']}...")

                text_to_analyze = ""
                if item["parsed_data"]:
                    try:
                        pdata = json.loads(item["parsed_data"])
                        text_to_analyze = pdata.get("description", "")
                    except:
                        pass

                if not text_to_analyze:
                    text_to_analyze = item["html_content"][:2000]

                result = classifier.classify_listing(text_to_analyze)

                db.save_lead(item["id"], result, job_id=job.job_id)
                classified_count += 1
                if result.get("is_private"):
                    private_count += 1

            on_log(
                f"Classification finished. Processed: {classified_count}, Private: {private_count}"
            )

            # 4. Export
            on_log("Exporting leads...")
            exporter = LeadExporter(db, self.artifact_manager)
            csv_path = exporter.export_new_leads(job.job_id)

            csv_generated = False
            if csv_path:
                from app.core.job_store import Artifact

                job.add_artifact(
                    Artifact(type="csv", label="New Private Leads", path=csv_path)
                )
                on_log(f"Exported leads to {csv_path}")
                csv_generated = True
            else:
                on_log("No new leads to export.")

            return {
                "scraped": total_new_count,
                "classified": classified_count,
                "private_found": private_count,
                "csv_generated": csv_generated,
            }
        except Exception as e:
            logger.exception("Workflow execution error")
            on_log(f"CRITICAL ERROR: {str(e)}")
            raise e

    def run(
        self,
        input_data: str,
        variant: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> MiniAppResult:
        """
        Legacy synchronous run method.
        Kept for compatibility with BaseMiniApp interface if used directly.
        """
        # Parse inputs
        try:
            inputs = json.loads(input_data) if input_data else {}
        except:
            inputs = {}

        # Create Job manually (synchronous mode)
        job = self.job_store.create(
            miniapp_id=self.metadata.id, input_data=inputs, variant=variant
        )

        # Shim for on_log
        def on_log(msg):
            self._log(job.job_id, msg)

        try:
            result_data = self.execute(job, on_log)
            job.complete(result_data)

            return self._create_result(
                status="ok",
                logs=job.logs,
                artifacts=[a.to_dict() for a in job.artifacts],
                result=job.result,
                completed_at=datetime.now(),
            )
        except Exception as e:
            job.fail(str(e))
            return self._create_result(
                status="error", logs=job.logs, artifacts=[], result={}, error=str(e)
            )
