import os
import sys

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.miniapps.market_scraper_privados.db import Database


def test_db():
    print("Testing Database...")

    # Use in-memory DB for test
    db = Database(":memory:")

    # 1. Save Raw Listing
    print("Saving raw listing...")
    uid = db.save_raw_listing("http://example.com/1", "<html></html>", "portal_a")
    assert uid is not None
    print(f"Saved listing ID: {uid}")

    # 2. Check Duplicates
    print("Checking duplicates...")
    uid2 = db.save_raw_listing("http://example.com/1", "<html></html>", "portal_a")
    assert uid2 is None
    print("Duplicate detection passed")

    # 3. Get Unclassified
    unclassified = db.get_unclassified_listings()
    assert len(unclassified) == 1
    print(f"Unclassified count: {len(unclassified)}")

    # 4. Save Lead (Private)
    print("Saving private lead...")
    classification = {
        "is_private": True,
        "confidence": 0.95,
        "contact_info": {"phone": "123456789"},
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


if __name__ == "__main__":
    test_db()
