import logging

logger = logging.getLogger(__name__)

from src.config import config

_r = config["rugpull"]
MAX_SELL_RATIO        = _r["max_sell_ratio"]
MIN_TRANSACTIONS_1H   = _r["min_transactions_1h"]
MAX_PRICE_CHANGE_1H   = _r["max_price_change_1h"]
MIN_LIQUIDITY_LOCKED  = _r["min_liquidity_locked"]
MAX_VOLUME_LIQ_RATIO  = _r["max_volume_liq_ratio"]


def check_sell_pressure(pair: dict) -> tuple[bool, str]:
    buys  = pair.get("buys_1h", 0)
    sells = pair.get("sells_1h", 0)

    if buys == 0 and sells > 0:
        return True, f"Tylko sprzedający w ostatniej godzinie ({sells} sells, 0 buys)"

    if buys > 0 and (sells / buys) > MAX_SELL_RATIO:
        ratio = sells / buys
        return True, f"Wysoka presja sprzedaży: {ratio:.1f}x więcej sells niż buys"

    return False, ""


def check_low_activity(pair: dict) -> tuple[bool, str]:
    buys  = pair.get("buys_1h", 0)
    sells = pair.get("sells_1h", 0)
    total = buys + sells

    if total < MIN_TRANSACTIONS_1H:
        return True, f"Bardzo mała aktywność: tylko {total} transakcji w 1h"

    return False, ""


def check_pump_and_dump(pair: dict) -> tuple[bool, str]:
    change_1h = pair.get("change_1h", 0)

    if change_1h > MAX_PRICE_CHANGE_1H:
        return True, f"Podejrzany wzrost ceny: +{change_1h:.0f}% w 1h (możliwy pump & dump)"

    return False, ""


def check_liquidity_trap(pair: dict) -> tuple[bool, str]:
    liquidity = pair.get("liquidity_usd", 0)

    if liquidity < MIN_LIQUIDITY_LOCKED:
        return True, f"Bardzo niska płynność: ${liquidity:,.0f} (łatwy rugpull)"

    return False, ""


def check_volume_liquidity_ratio(pair: dict) -> tuple[bool, str]:
    liquidity  = pair.get("liquidity_usd", 0)
    volume_24h = pair.get("volume_24h", 0)

    if liquidity <= 0:
        return False, ""

    ratio = volume_24h / liquidity

    if ratio > MAX_VOLUME_LIQ_RATIO:
        return True, f"Podejrzany stosunek wolumen/płynność: {ratio:.1f}x"

    return False, ""


def check_no_socials(pair: dict) -> tuple[bool, str]:
    info = pair.get("info") or {}
    socials  = info.get("socials", []) or []
    websites = info.get("websites", []) or []

    if not socials and not websites:
        return True,

    return False, ""

CHECKS = [
    check_sell_pressure,
    check_low_activity,
    check_pump_and_dump,
    check_liquidity_trap,
    check_volume_liquidity_ratio,
    check_no_socials,
]


def analyze_rugpull_risk(pair: dict) -> dict:
    warnings = []

    for check in CHECKS:
        try:
            is_risky, reason = check(pair)
            if is_risky:
                warnings.append(reason)
        except Exception as e:
            logger.debug(f"Błąd sprawdzenia: {e}")
            continue

    risk_score = min(len(warnings) * 20, 100)

    if risk_score == 0:
        risk_level = "LOW"
    elif risk_score <= 40:
        risk_level = "MEDIUM"
    elif risk_score <= 60:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    is_safe = risk_score <= _r["max_safe_risk_score"]

    if warnings:
        logger.debug(
            f"[{pair.get('name', '?')}] Ryzyko {risk_level} "
            f"(score: {risk_score}) — {len(warnings)} ostrzeżeń"
        )

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "warnings":   warnings,
        "is_safe":    is_safe,
    }