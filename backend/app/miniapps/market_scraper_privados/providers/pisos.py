from typing import List, Optional
from .base import BaseProvider, ListingMetadata, RawListingData
import logging

logger = logging.getLogger(__name__)


class PisosProvider(BaseProvider):
    """
    Adapter for Pisos.com.
    """

    @property
    def name(self) -> str:
        return "pisos.com"

    @property
    def base_url(self) -> str:
        return "https://www.pisos.com"

    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        logger.info(f"Searching Pisos.com for {city} (max {max_items})...")

        results = []
        # Mocking listings
        for i in range(1, 3):
            if len(results) >= max_items:
                break
            results.append(
                ListingMetadata(
                    external_id=f"pisos_{i}",
                    url=f"https://www.pisos.com/comprar/piso-{city}/{i}/",
                    title=f"Ático en {city} - Pisos.com {i}",
                    price="300.000 €",
                    location=city,
                )
            )

        return results

    def fetch_details(self, url: str) -> Optional[RawListingData]:
        logger.info(f"Fetching Pisos.com details: {url}")

        html = """
        <html>
            <body>
                <h1 class="title">Ático espectacular</h1>
                <div class="price">300.000 €</div>
                <div class="description">
                    Venta directa de propietario.
                    Ático con terraza de 50m2.
                    Abstenerse agencias.
                </div>
            </body>
        </html>
        """

        return RawListingData(
            url=url,
            html_content=html,
            parsed_data={
                "title": "Ático espectacular",
                "price": "300.000 €",
                "description": "Venta directa de propietario. Ático con terraza de 50m2. Abstenerse agencias.",
            },
        )
