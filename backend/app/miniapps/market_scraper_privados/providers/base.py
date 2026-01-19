from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict
import random
import time
import httpx
import logging

logger = logging.getLogger(__name__)


@dataclass
class ListingMetadata:
    """Basic info about a listing found in search results."""

    external_id: str
    url: str
    title: str
    price: Optional[str] = None
    location: Optional[str] = None


@dataclass
class RawListingData:
    """Detailed data scraped from a listing."""

    url: str
    html_content: str
    parsed_data: Dict  # Structured data (title, price, description, etc.)


class BaseProvider(ABC):
    """Abstract base class for all portal providers."""

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def _sleep_random(self, min_seconds: float = 1.0, max_seconds: float = 3.0):
        """Sleep for a random amount of time to be polite."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def _get_html(self, url: str) -> Optional[str]:
        """Fetch HTML content from a URL with basic error handling."""
        try:
            self._sleep_random()
            with httpx.Client(timeout=30.0, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
                response.raise_for_status()
                return response.text
        except httpx.HTTPError as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return None

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name (e.g., 'idealista')."""
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base URL of the portal."""
        pass

    @abstractmethod
    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        """
        Search for listings in a city/zone.
        Returns a list of metadata (URL, ID, etc.).
        """
        pass

    @abstractmethod
    def fetch_details(self, url: str) -> Optional[RawListingData]:
        """
        Fetch full details of a specific listing.
        Returns None if fetching fails.
        """
        pass
