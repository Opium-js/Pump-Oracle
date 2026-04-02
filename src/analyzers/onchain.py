import pandas as pd
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


# ── Kryteria filtrowania ────────────────────────────────────────────────────
MIN_LIQUIDITY_USD   = 5_000   # minimalna płynność
MIN_VOLUME_24H      = 10_000   # minimalny wolumen 24h
MAX_PAIR_AGE_HOURS  = 72       # max wiek pary w godzinach
MIN_PRICE_CHANGE_1H = 5.0     # minimalny wzrost ceny w ciągu 1h (%)
MIN_BUY_SELL_RATIO  = 1.1     # więcej kupujących niż sprzedających


def parse_pair(pair: dict) -> dict | None:
    try:
        liquidity  = (pair.get("liquidity") or {}).get("usd", 0) or 0
        volume_24h = (pair.get("volume") or {}).get("h24", 0) or 0
        volume_1h  = (pair.get("volume") or {}).get("h1", 0) or 0
        change_1h  = (pair.get("priceChange") or {}).get("h1", 0) or 0
        change_24h = (pair.get("priceChange") or {}).get("h24", 0) or 0
        txns_h1    = (pair.get("txns") or {}).get("h1", {})
        buys_1h    = txns_h1.get("buys", 0) or 0
        sells_1h   = txns_h1.get("sells", 0) or 0

        base  = pair.get("baseToken") or {}
        quote = pair.get("quoteToken") or {}

        created_at = pair.get("pairCreatedAt")
        if created_at:
            created_dt = datetime.fromtimestamp(created_at / 1000, tz=timezone.utc)
            age_hours  = (datetime.now(timezone.utc) - created_dt).total_seconds() / 3600
        else:
            age_hours  = None
            created_dt = None

        return {
            "pair_address":  pair.get("pairAddress", ""),
            "dex":           pair.get("dexId", ""),
            "name":          f"{base.get('symbol','?')}/{quote.get('symbol','?')}",
            "base_symbol":   base.get("symbol", "?"),
            "base_address":  base.get("address", ""),
            "price_usd":     float(pair.get("priceUsd") or 0),
            "liquidity_usd": float(liquidity),
            "volume_24h":    float(volume_24h),
            "volume_1h":     float(volume_1h),
            "change_1h":     float(change_1h),
            "change_24h":    float(change_24h),
            "buys_1h":       int(buys_1h),
            "sells_1h":      int(sells_1h),
            "age_hours":     age_hours,
            "created_at":    created_dt,
            "url":           pair.get("url", ""),
        }
    except Exception as e:
        logger.debug(f"Błąd parsowania pary: {e}")
        return None


def calculate_buy_sell_ratio(parsed: dict) -> float:
    sells = parsed["sells_1h"]
    if sells == 0:
        return float("inf") if parsed["buys_1h"] > 0 else 0.0
    return parsed["buys_1h"] / sells


def is_interesting(parsed: dict) -> tuple[bool, list[str]]:
    reasons = []

    if parsed["liquidity_usd"] < MIN_LIQUIDITY_USD:
        reasons.append(f"Za mała płynność: ${parsed['liquidity_usd']:,.0f}")

    if parsed["volume_24h"] < MIN_VOLUME_24H:
        reasons.append(f"Za mały wolumen 24h: ${parsed['volume_24h']:,.0f}")

    if parsed["age_hours"] is None:
        reasons.append("Brak danych o wieku pary")
    elif parsed["age_hours"] > MAX_PAIR_AGE_HOURS:
        reasons.append(f"Para za stara: {parsed['age_hours']:.1f}h > {MAX_PAIR_AGE_HOURS}h")

    if parsed["change_1h"] < MIN_PRICE_CHANGE_1H:
        reasons.append(f"Za mały wzrost 1h: {parsed['change_1h']:.1f}%")

    ratio = calculate_buy_sell_ratio(parsed)
    if ratio < MIN_BUY_SELL_RATIO:
        reasons.append(f"Za mało kupujących vs sprzedających: {ratio:.2f}")

    return (len(reasons) == 0, reasons)


def analyze_pairs(raw_pairs: list[dict]) -> pd.DataFrame:
    parsed_list = []
    for raw in raw_pairs:
        parsed = parse_pair(raw)
        if parsed:
            parsed_list.append(parsed)

    if not parsed_list:
        logger.warning("Brak par do analizy")
        return pd.DataFrame()

    df = pd.DataFrame(parsed_list)

    # Dodaj kolumny wyliczane
    df["buy_sell_ratio"] = df.apply(calculate_buy_sell_ratio, axis=1)
    df["interesting"]    = df.apply(lambda r: is_interesting(r)[0], axis=1)

    total       = len(df)
    interesting = df["interesting"].sum()
    logger.info(f"Przeanalizowano {total} par → {interesting} ciekawych")

    return df


def get_interesting_pairs(raw_pairs: list[dict]) -> list[dict]:
    df = analyze_pairs(raw_pairs)

    if df.empty:
        return []

    interesting_df = df[df["interesting"]].sort_values(
        "volume_24h", ascending=False
    )

    return interesting_df.to_dict(orient="records")