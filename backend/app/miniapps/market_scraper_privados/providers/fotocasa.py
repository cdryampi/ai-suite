from typing import List, Optional
from .base import BaseProvider, ListingMetadata, RawListingData
import logging

logger = logging.getLogger(__name__)


class FotocasaProvider(BaseProvider):
    """
    Adapter for Fotocasa.
    """

    @property
    def name(self) -> str:
        return "fotocasa"

    @property
    def base_url(self) -> str:
        return "https://www.fotocasa.es"

    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        logger.info(f"Searching Fotocasa for {city} (max {max_items})...")

        # Mock logic for demonstration
        results = []
        # Mocking 2 listings
        for i in range(1, 3):
            if len(results) >= max_items:
                break
            results.append(
                ListingMetadata(
                    external_id=f"foto_{i}",
                    url=f"https://www.fotocasa.es/es/comprar/vivienda/{city}/123{i}/123{i}/",
                    title=f"Apartamento en {city} - Fotocasa {i}",
                    price="180.000 €",
                    location=city,
                )
            )

        return results

    def fetch_details(self, url: str) -> Optional[RawListingData]:
        logger.info(f"Fetching Fotocasa details: {url}")

        # Mock HTML
        html = """
        <html>
            <body>
                <h1 class="re-DetailHeader-propertyTitle">Apartamento luminoso</h1>
                <div class="re-DetailHeader-price">180.000 €</div>
                <div class="re-DetailDescription">
                    Venta de particular a particular. Sin comisiones.
                    Piso reformado en zona tranquila.
                    Contactar por whatsap al 611 222 333.
                </div>
            </body>
        </html>
        """

        return RawListingData(
            url=url,
            html_content=html,
            parsed_data={
                "title": "Apartamento luminoso",
                "price": "180.000 €",
                "description": "Venta de particular a particular. Sin comisiones. Piso reformado en zona tranquila. Contactar por whatsap al 611 222 333.",
            },
        )
