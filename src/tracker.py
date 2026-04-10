import logging
import time
import requests

from src.database import get_tokens_to_check, update_token_price

logger = logging.getLogger(__name__)

BASE_URL = "https://api.dexscreener.com"


def get_current_price(pair_address: str) -> float | None:
    url = f"{BASE_URL}/latest/dex/pairs/solana/{pair_address}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        pair = data.get("pair") or {}
        price = pair.get("priceUsd")
        return float(price) if price else None
    except Exception as e:
        logger.error(f"Błąd pobierania ceny dla {pair_address[:8]}: {e}")
        return None


def check_tracked_tokens() -> None:
    tokens = get_tokens_to_check()

    if not tokens:
        logger.info("Brak tokenów do sprawdzenia")
        return

    logger.info(f"Sprawdzam ceny {len(tokens)} tokenów...")

    for token in tokens:
        pair_address = token["pair_address"]
        current_price = get_current_price(pair_address)

        if current_price is None:
            logger.warning(f"Nie można pobrać ceny dla {token['name']}")
            continue

        price_at_found = float(token["price_at_found"])

        if token["checked_1h_at"] is None:
            update_token_price(token["id"], "1h", current_price, price_at_found)

        if token["checked_6h_at"] is None:
            update_token_price(token["id"], "6h", current_price, price_at_found)

        if token["checked_24h_at"] is None:
            update_token_price(token["id"], "24h", current_price, price_at_found)

        time.sleep(0.3)