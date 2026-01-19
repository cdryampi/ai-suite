import os
import sys
import tempfile

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.miniapps.market_scraper_privados.db import Database


def test_db():
    print("Testing Database...")

    # Use temp file for test to ensure persistence across connections
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        db_path = tmp.name

    try:
        db = Database(db_path)

        # 1. Save Raw Listing
        print("Saving raw listing...")
        uid = db.save_raw_listing(
            url="http://example.com/1",
            source="portal_a",
            html_content="<html></html>",
            external_id="ext_1",
        )
        assert uid is not None
        print(f"Saved listing ID: {uid}")

        # 2. Check Duplicates
        print("Checking duplicates...")
        uid2 = db.save_raw_listing(
            url="http://example.com/1", source="portal_a", html_content="<html></html>"
        )
        assert uid2 is None
        print("Duplicate detection passed")

        # 3. Get Unclassified (method name changed to get_pending_listings)
        unclassified = db.get_pending_listings()
        assert len(unclassified) == 1
        print(f"Unclassified count: {len(unclassified)}")

        # 4. Save Lead (Private)
        print("Saving private lead...")
        classification = {
            "is_private": True,
            "confidence": 0.95,
            "owner_name": "Juan",
            "phone": "123456789",
            "notes": "Test note",
        }
        lead_id = db.save_lead(uid, classification)
        print(f"Saved Lead ID: {lead_id}")

        # 5. Get New Leads
        new_leads = db.get_new_leads()
        assert len(new_leads) == 1
        assert new_leads[0]["url"] == "http://example.com/1"
        print("Get new leads passed")

        # 6. Mark Exported
        print("Marking exported...")
        db.mark_leads_exported([lead_id])

        new_leads_after = db.get_new_leads()
        assert len(new_leads_after) == 0
        print("Export status update passed")

        print("All DB tests passed!")

    finally:
        if os.path.exists(db_path):
            try:
                os.unlink(db_path)
            except:
                pass


if __name__ == "__main__":
    test_db()
