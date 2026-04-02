import requests
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.dexscreener.com"

# Znane adresy quote tokenów na Solanie (pary memecoin/SOL są najczęstsze)
WSOL = "So11111111111111111111111111111111111111112"


def get_boosted_tokens() -> list[dict]:
    urls = [
        f"{BASE_URL}/token-boosts/latest/v1",
        f"{BASE_URL}/token-boosts/top/v1",
    ]

    all_pairs = []
    seen = set()

    for url in urls:
        try:
            logger.info(f"Pobieram: {url}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            tokens = data if isinstance(data, list) else []
            solana_tokens = [t for t in tokens if t.get("chainId") == "solana"]
            logger.info(f"Znaleziono {len(solana_tokens)} boosted tokenów na Solanie")

            for token in solana_tokens[:20]:
                addr = token.get("tokenAddress", "")
                if not addr or addr in seen:
                    continue
                seen.add(addr)

                pairs = get_pairs_for_token(addr)
                all_pairs.extend(pairs)
                time.sleep(0.2)

        except requests.exceptions.RequestException as e:
            logger.error(f"Błąd {url}: {e}")

    return all_pairs


def get_pairs_for_token(token_address: str) -> list[dict]:
    url = f"{BASE_URL}/token-pairs/v1/solana/{token_address}"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        pairs = data if isinstance(data, list) else data.get("pairs", [])
        return pairs

    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd pobierania par dla {token_address[:8]}: {e}")
        return []


def get_latest_token_profiles() -> list[dict]:
    url = f"{BASE_URL}/token-profiles/latest/v1"
    all_pairs = []
    seen = set()

    try:
        logger.info("Pobieram najnowsze profile tokenów...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        tokens = data if isinstance(data, list) else []
        solana_tokens = [t for t in tokens if t.get("chainId") == "solana"]
        logger.info(f"Znaleziono {len(solana_tokens)} nowych profili na Solanie")

        for token in solana_tokens[:20]:
            addr = token.get("tokenAddress", "")
            if not addr or addr in seen:
                continue
            seen.add(addr)

            pairs = get_pairs_for_token(addr)
            all_pairs.extend(pairs)
            time.sleep(0.2)

    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd pobierania profili: {e}")

    return all_pairs


def get_new_solana_pairs() -> list[dict]:
    all_pairs = []
    seen = set()

    logger.info("=== Pobieram boosted tokeny ===")
    boosted = get_boosted_tokens()
    for p in boosted:
        addr = p.get("pairAddress", "")
        if addr and addr not in seen:
            seen.add(addr)
            all_pairs.append(p)

    logger.info("=== Pobieram najnowsze profile ===")
    profiles = get_latest_token_profiles()
    for p in profiles:
        addr = p.get("pairAddress", "")
        if addr and addr not in seen:
            seen.add(addr)
            all_pairs.append(p)

    logger.info(f"=== Łącznie unikalnych par: {len(all_pairs)} ===")
    return all_pairs