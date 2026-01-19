import csv
import logging
import os
from datetime import datetime
from typing import List, Optional

from app.core.job_store import JobStore
from .db import Database

logger = logging.getLogger(__name__)


class LeadExporter:
    """
    Exports validated private leads to CSV.
    """

    def __init__(self, db: Database, artifact_manager):
        self.db = db
        self.artifact_manager = artifact_manager

    def export_new_leads(self, job_id: str) -> Optional[str]:
        """
        Query new leads, write to CSV, mark as exported.
        Returns the path to the generated artifact or None if no leads.
        """
        leads = self.db.get_new_leads()

        if not leads:
            logger.info("No new leads to export.")
            return None

        # Prepare CSV data
        fieldnames = [
            "Contact Name",
            "Phone",
            "Notes",
            "Confidence",
            "URL",
            "Price",
            "Location",
            "Title",
            "Date Scraped",
        ]

        rows = []
        lead_ids = []

        for lead in leads:
            parsed = lead.get("parsed_data", {})
            rows.append(
                {
                    "Contact Name": lead.get("contact_name") or "N/A",
                    "Phone": lead.get("contact_phone") or "N/A",
                    "Notes": lead.get("notes") or "",
                    "Confidence": f"{lead.get('confidence', 0):.2f}",
                    "URL": lead.get("url"),
                    "Price": parsed.get("price", "N/A"),
                    "Location": parsed.get("location", "N/A"),
                    "Title": parsed.get("title", "N/A"),
                    "Date Scraped": lead.get("created_at"),
                }
            )
            lead_ids.append(lead["id"])

        # Generate CSV string
        # We use a simple string buffer or write directly to file via manager
        # ArtifactManager usually takes data or file path.
        # Let's assume we create the content and pass it to save_text (or save_artifact if raw).
        # We'll construct the CSV content first.

        import io

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        csv_content = output.getvalue()

        filename = f"leads_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        # Save artifact
        # Assuming artifact_manager.save_text can handle this, or save_file
        # BaseMiniApp uses artifact_manager.save_text in previous examples
        artifact_path = self.artifact_manager.save_text(
            job_id=job_id, filename=filename, content=csv_content
        )

        # Mark as exported
        self.db.mark_leads_exported(lead_ids)

        return artifact_path
