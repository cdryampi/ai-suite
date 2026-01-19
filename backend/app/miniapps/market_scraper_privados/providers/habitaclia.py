from typing import List, Optional
from .base import BaseProvider, ListingMetadata, RawListingData
import logging

logger = logging.getLogger(__name__)


class HabitacliaProvider(BaseProvider):
    """
    Adapter for Habitaclia.
    """

    @property
    def name(self) -> str:
        return "habitaclia"

    @property
    def base_url(self) -> str:
        return "https://www.habitaclia.com"

    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        logger.info(f"Searching Habitaclia for {city} (max {max_items})...")

        results = []
        # Mocking listings
        for i in range(1, 3):
            if len(results) >= max_items:
                break
            results.append(
                ListingMetadata(
                    external_id=f"habi_{i}",
                    url=f"https://www.habitaclia.com/comprar-vivienda-{city}/i{i}.htm",
                    title=f"Casa en {city} - Habitaclia {i}",
                    price="195.000 €",
                    location=city,
                )
            )

        return results

    def fetch_details(self, url: str) -> Optional[RawListingData]:
        logger.info(f"Fetching Habitaclia details: {url}")

        html = """
        <html>
            <body>
                <h1 class="summary-title">Casa adosada en venta</h1>
                <div class="summary-price">195.000 €</div>
                <div class="description">
                    Abstenerse inmobiliarias.
                    Casa de pueblo reformada.
                    Llamar tardes: 622 333 444 (Maria).
                </div>
            </body>
        </html>
        """

        return RawListingData(
            url=url,
            html_content=html,
            parsed_data={
                "title": "Casa adosada en venta",
                "price": "195.000 €",
                "description": "Abstenerse inmobiliarias. Casa de pueblo reformada. Llamar tardes: 622 333 444 (Maria).",
            },
        )
