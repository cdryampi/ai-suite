from typing import List, Optional
from .base import BaseProvider, ListingMetadata, RawListingData
import logging

logger = logging.getLogger(__name__)


class WallapopProvider(BaseProvider):
    """
    Adapter for Wallapop (Inmobiliaria).
    """

    @property
    def name(self) -> str:
        return "wallapop"

    @property
    def base_url(self) -> str:
        return "https://es.wallapop.com"

    def search(self, city: str, max_items: int = 10) -> List[ListingMetadata]:
        logger.info(f"Searching Wallapop for {city} (max {max_items})...")

        results = []
        # Mocking listings
        for i in range(1, 3):
            if len(results) >= max_items:
                break
            results.append(
                ListingMetadata(
                    external_id=f"walla_{i}",
                    url=f"https://es.wallapop.com/item/piso-en-{city}-{i}",
                    title=f"Oportunidad en {city} - Wallapop {i}",
                    price="120.000 €",
                    location=city,
                )
            )

        return results

    def fetch_details(self, url: str) -> Optional[RawListingData]:
        logger.info(f"Fetching Wallapop details: {url}")

        html = """
        <html>
            <body>
                <h1 class="card-product-detail-title">Oportunidad</h1>
                <div class="card-product-detail-price">120.000 €</div>
                <div class="card-product-detail-description">
                    Vendo mi piso por cambio de ciudad.
                    Urge venta.
                    Soy particular.
                    Escribir por chat.
                </div>
            </body>
        </html>
        """

        return RawListingData(
            url=url,
            html_content=html,
            parsed_data={
                "title": "Oportunidad",
                "price": "120.000 €",
                "description": "Vendo mi piso por cambio de ciudad. Urge venta. Soy particular. Escribir por chat.",
            },
        )
