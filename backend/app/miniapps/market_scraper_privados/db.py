import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

DB_FILENAME = "market_scraper.db"


class Database:
    """
    Persistence layer for Market Scraper (Privados).
    Uses SQLite to store raw listings and validated leads.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to the database file. If None, uses default in package dir.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            # Default to storage directory or package directory
            base_dir = Path(__file__).parent.parent.parent.parent / "data"
            base_dir.mkdir(exist_ok=True, parents=True)
            self.db_path = base_dir / DB_FILENAME

        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """Get a configured database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Allow accessing columns by name
        return conn

    def _init_db(self):
        """Initialize the database schema."""
        conn = self._get_conn()
        cursor = conn.cursor()

        # 1. RawListing Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                external_id TEXT,
                url TEXT UNIQUE NOT NULL,
                html_content TEXT,
                parsed_data TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending_classification'
            )
        """)

        # Index for faster lookups
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_raw_status ON raw_listings(status)"
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_url ON raw_listings(url)")

        # 2. Lead Table
        # status: 'new', 'exported', 'called', 'discarded'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_listing_id INTEGER NOT NULL,
                is_private BOOLEAN NOT NULL CHECK (is_private IN (0, 1)),
                confidence REAL,
                contact_name TEXT,
                contact_phone TEXT,
                notes TEXT,
                status TEXT DEFAULT 'new',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exported_at TIMESTAMP,
                FOREIGN KEY (raw_listing_id) REFERENCES raw_listings (id)
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_lead_status ON leads(status)")

        conn.commit()
        conn.close()

    # ----------------------------------------------------------------
    # RawListing Operations
    # ----------------------------------------------------------------

    def save_raw_listing(
        self,
        url: str,
        source: str,
        html_content: str,
        external_id: Optional[str] = None,
        parsed_data: Optional[Dict] = None,
    ) -> Optional[int]:
        """
        Save a raw listing. Returns ID if inserted, None if duplicate.
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        parsed_json = (
            json.dumps(parsed_data, ensure_ascii=False) if parsed_data else None
        )

        try:
            cursor.execute(
                """
                INSERT INTO raw_listings (url, source, external_id, html_content, parsed_data)
                VALUES (?, ?, ?, ?, ?)
            """,
                (url, source, external_id, html_content, parsed_json),
            )
            listing_id = cursor.lastrowid
            conn.commit()
            return listing_id
        except sqlite3.IntegrityError:
            # Duplicate URL
            return None
        finally:
            conn.close()

    def exists_listing(self, url: str) -> bool:
        """Check if a URL has already been scraped."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM raw_listings WHERE url = ?", (url,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists

    def get_pending_listings(self, limit: int = 10) -> List[dict]:
        """Get listings pending classification."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT * FROM raw_listings 
            WHERE status = 'pending_classification'
            LIMIT ?
        """,
            (limit,),
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update_listing_status(self, listing_id: int, status: str):
        """Update status of a raw listing."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE raw_listings SET status = ? WHERE id = ?", (status, listing_id)
        )
        conn.commit()
        conn.close()

    # ----------------------------------------------------------------
    # Lead Operations
    # ----------------------------------------------------------------

    def save_lead(self, listing_id: int, classification_data: dict) -> int:
        """
        Save a classification result as a Lead.
        """
        is_private = classification_data.get("is_private", False)
        confidence = classification_data.get("confidence", 0.0)

        contact_name = classification_data.get("owner_name")
        contact_phone = classification_data.get("phone")
        notes = classification_data.get("notes")

        conn = self._get_conn()
        cursor = conn.cursor()

        # Insert lead
        cursor.execute(
            """
            INSERT INTO leads (raw_listing_id, is_private, confidence, contact_name, contact_phone, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (listing_id, is_private, confidence, contact_name, contact_phone, notes),
        )

        lead_id = cursor.lastrowid

        # Update raw listing status
        cursor.execute(
            """
            UPDATE raw_listings SET status = 'classified' WHERE id = ?
        """,
            (listing_id,),
        )

        conn.commit()
        conn.close()
        return lead_id

    def get_new_leads(self) -> List[dict]:
        """Get validated private leads that haven't been exported."""
        conn = self._get_conn()
        cursor = conn.cursor()

        query = """
            SELECT l.*, r.url, r.source, r.parsed_data
            FROM leads l
            JOIN raw_listings r ON l.raw_listing_id = r.id
            WHERE l.is_private = 1 AND l.status = 'new'
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            d = dict(row)
            if d.get("parsed_data"):
                try:
                    d["parsed_data"] = json.loads(d["parsed_data"])
                except:
                    d["parsed_data"] = {}
            results.append(d)

        conn.close()
        return results

    def mark_leads_exported(self, lead_ids: List[int]):
        """Mark leads as exported."""
        if not lead_ids:
            return

        conn = self._get_conn()
        placeholders = ",".join("?" * len(lead_ids))
        timestamp = datetime.now().isoformat()

        conn.execute(
            f"""
            UPDATE leads 
            SET status = 'exported', exported_at = ?
            WHERE id IN ({placeholders})
        """,
            (timestamp, *lead_ids),
        )

        conn.commit()
        conn.close()
