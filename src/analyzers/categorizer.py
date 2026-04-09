import logging

logger = logging.getLogger(__name__)

TAG_NEW_MAX_AGE_HOURS    = 6      # "nowy" — wiek < 6h
TAG_HOT_MIN_CHANGE_1H    = 100.0  # "gorący" — zmiana 1h > 100%
TAG_RISKY_MIN_SCORE      = 20     # "ryzykowny" — risk_score > 20
TAG_WHALE_MIN_LIQUIDITY  = 100_000 # "wieloryb" — płynność > $100k
TAG_MICRO_MAX_LIQUIDITY  = 10_000  # "mikro" — płynność < $10k


def categorize_token(pair: dict) -> list[str]:
    tags = []

    age_hours    = pair.get("age_hours") or 0
    change_1h    = pair.get("change_1h", 0)
    risk_score   = pair.get("risk_score", 0)
    liquidity    = pair.get("liquidity_usd", 0)

    if age_hours < TAG_NEW_MAX_AGE_HOURS:
        tags.append("nowy")

    if change_1h > TAG_HOT_MIN_CHANGE_1H:
        tags.append("gorący")

    if risk_score > TAG_RISKY_MIN_SCORE:
        tags.append("ryzykowny")

    if liquidity >= TAG_WHALE_MIN_LIQUIDITY:
        tags.append("wieloryb")
    elif liquidity < TAG_MICRO_MAX_LIQUIDITY:
        tags.append("mikro")

    logger.debug(f"[{pair.get('name', '?')}] Tagi: {tags}")
    return tags


TAG_EMOJIS = {
    "nowy":      "🆕",
    "gorący":    "🔥",
    "ryzykowny": "⚠️",
    "wieloryb":  "🐋",
    "mikro":     "🔬",
}


def format_tags(tags: list[str]) -> str:
    if not tags:
        return ""
    return " ".join(TAG_EMOJIS.get(tag, "") + tag for tag in tags)