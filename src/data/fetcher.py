import requests
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.dexscreener.com"

SOLANA_BASE_TOKENS = [
    "So11111111111111111111111111111111111111112",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
]


def get_pairs_by_token(token_address: str) -> list[dict]:
    url = f"{BASE_URL}/token-pairs/v1/solana/{token_address}"

    try:
        logger.info(f"Pobieram pary dla tokena: {token_address[:8]}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, list):
            pairs = data
        else:
            pairs = data.get("pairs", [])

        logger.info(f"Pobrano {len(pairs)} par")
        return pairs

    except requests.exceptions.Timeout:
        logger.error("Timeout - API nie odpowiada")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd połączenia z API: {e}")
        return []


def get_new_solana_pairs() -> list[dict]:
    all_pairs = []
    seen = set()

    for token in SOLANA_BASE_TOKENS:
        pairs = get_pairs_by_token(token)
        for pair in pairs:
            addr = pair.get("pairAddress", "")
            if addr and addr not in seen:
                seen.add(addr)
                all_pairs.append(pair)

    logger.info(f"Łącznie unikalnych par: {len(all_pairs)}")
    return all_pairs


def search_pairs(query: str) -> list[dict]:
    url = f"{BASE_URL}/latest/dex/search"

    try:
        response = requests.get(url, params={"q": query}, timeout=10)
        response.raise_for_status()
        data = response.json()
        pairs = data.get("pairs", [])

        return [p for p in pairs if p.get("chainId") == "solana"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd wyszukiwania: {e}")
        return []