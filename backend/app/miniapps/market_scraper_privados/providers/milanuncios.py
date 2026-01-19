from typing import List, Optional
from .base import BaseProvider, ListingMetadata, RawListingData
import logging

logger = logging.getLogger(__name__)


class MilanunciosProvider(BaseProvider):
    """
    Adapter for Milanuncios (Inmobiliaria).
    """

    @property
    def name(self) -> str:
        return "milanuncios"

    @property
    def base_url(self) -> str:
        return "https://www.milanuncios.com"

    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        logger.info(f"Searching Milanuncios for {city} (max {max_items})...")

        results = []
        # Mocking listings
        for i in range(1, 3):
            if len(results) >= max_items:
                break
            results.append(
                ListingMetadata(
                    external_id=f"mila_{i}",
                    url=f"https://www.milanuncios.com/venta-de-pisos-en-{city}/anuncio-{i}.htm",
                    title=f"Piso barato en {city} - Milanuncios {i}",
                    price="150.000 €",
                    location=city,
                )
            )

        return results

    def fetch_details(self, url: str) -> Optional[RawListingData]:
        logger.info(f"Fetching Milanuncios details: {url}")

        html = """
        <html>
            <body>
                <h1 class="ad-detail-title">Piso barato</h1>
                <div class="ad-detail-price">150.000 €</div>
                <div class="ad-detail-description">
                    Soy particular. Vendo urgente por traslado.
                    Piso para entrar a vivir.
                    Tel 633 444 555.
                </div>
            </body>
        </html>
        """

        return RawListingData(
            url=url,
            html_content=html,
            parsed_data={
                "title": "Piso barato",
                "price": "150.000 €",
                "description": "Soy particular. Vendo urgente por traslado. Piso para entrar a vivir. Tel 633 444 555.",
            },
        )
