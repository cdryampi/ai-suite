import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional

from app.miniapps.base import BaseMiniApp, MiniAppMetadata, MiniAppResult
from .db import Database
from .classifier import ListingClassifier
from .exporter import LeadExporter
from .providers.idealista import IdealistaProvider
from .providers.fotocasa import FotocasaProvider
from .providers.habitaclia import HabitacliaProvider
from .providers.milanuncios import MilanunciosProvider

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
            version="1.2.0",
            author="Sttil Team",
            tags=["real-estate", "scraper", "lead-gen"],
            variants={
                1: "Default - Top 4 Portals (Idealista, Fotocasa, Habitaclia, Milanuncios)"
            },
        )

    def run(
        self,
        input_data: str,
        variant: int = 1,
        options: Optional[Dict[str, Any]] = None,
    ) -> MiniAppResult:
        """
        Executes the full pipeline.

        input_data: JSON string with configuration (e.g., {"city": "Madrid", "max_items": 10})
        """
        started_at = datetime.now()
        logs = []
        artifacts = []

        # Parse inputs
        try:
            inputs = json.loads(input_data) if input_data else {}
        except:
            inputs = {}

        city = inputs.get("city", "madrid")
        max_items = int(inputs.get("max_items", 5))

        # Create Job
        job = self.job_store.create(
            miniapp_id=self.metadata.id, input_data=inputs, variant=variant
        )
        job_id = job.job_id

        self._log(job_id, f"Starting Market Scraper for {city} (Max: {max_items})")
        logs.append("Job started")

        try:
            # 1. Initialize DB
            db = Database()

            # 2. Scraping (Multi-provider)
            self._log(job_id, "Starting scraping phase...")

            providers = [
                IdealistaProvider(),
                FotocasaProvider(),
                HabitacliaProvider(),
                MilanunciosProvider(),
            ]

            total_new_count = 0

            for provider in providers:
                self._log(job_id, f"Running provider: {provider.name}...")
                try:
                    found_listings = provider.search(city, max_items)
                    self._log(
                        job_id, f"Found {len(found_listings)} items on {provider.name}"
                    )

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
                    self._log(job_id, f"Error running {provider.name}: {e}")

            self._log(
                job_id, f"Scraping finished. Total new listings: {total_new_count}"
            )
            logs.append(f"Scraped {total_new_count} new listings")

            # 3. Classification
            self._log(job_id, "Starting classification phase...")
            classifier = ListingClassifier(self.llm_client)
            pending = db.get_pending_listings()

            classified_count = 0
            private_count = 0

            for item in pending:
                # self._log(job_id, f"Classifying {item['url']}...")
                # Use parsed data description if available, else HTML (stripped)
                # For this demo, we assume parsed_data['description'] or we might need to parse HTML here
                # But provider should have parsed it.

                text_to_analyze = ""
                if item["parsed_data"]:
                    try:
                        pdata = json.loads(item["parsed_data"])
                        text_to_analyze = pdata.get("description", "")
                    except:
                        pass

                if not text_to_analyze:
                    # Fallback to HTML (simple strip)
                    # Ideally use BeautifulSoup but let's keep it simple or assume provider did it
                    text_to_analyze = item["html_content"][:2000]  # Raw truncation

                result = classifier.classify_listing(text_to_analyze)

                db.save_lead(item["id"], result)
                classified_count += 1
                if result.get("is_private"):
                    private_count += 1

            self._log(
                job_id,
                f"Classification finished. Processed: {classified_count}, Private: {private_count}",
            )
            logs.append(
                f"Classified {classified_count} listings ({private_count} private)"
            )

            # 4. Export
            self._log(job_id, "Exporting leads...")
            exporter = LeadExporter(db, self.artifact_manager)
            csv_path = exporter.export_new_leads(job_id)

            if csv_path:
                artifacts.append(
                    {"type": "csv", "label": "New Private Leads", "path": csv_path}
                )
                self._log(job_id, f"Exported leads to {csv_path}")
            else:
                self._log(job_id, "No new leads to export.")

            # Complete
            job.complete(
                result={
                    "scraped": total_new_count,
                    "classified": classified_count,
                    "private_found": private_count,
                    "csv_generated": bool(csv_path),
                }
            )

            return self._create_result(
                status="ok",
                logs=job.logs,
                artifacts=artifacts,
                result=job.result,
                completed_at=datetime.now(),
            )

        except Exception as e:
            logger.exception("Workflow failed")
            error_msg = str(e)
            job.fail(error_msg)
            return self._create_result(
                status="error",
                logs=job.logs,
                artifacts=artifacts,
                result={},
                error=error_msg,
            )
