import logging

logger = logging.getLogger(__name__)

# ── Progi rugpull detection ─────────────────────────────────────────────────
MAX_SELL_RATIO        = 3.0    # sells/buys > 3 = podejrzane
MIN_TRANSACTIONS_1H   = 10     # za mało transakcji = martwy token
MAX_PRICE_CHANGE_1H   = 1000.0 # +1000% w 1h = prawdopodobny pump & dump
MIN_LIQUIDITY_LOCKED  = 1000   # płynność poniżej $1k = łatwy rugpull
MAX_VOLUME_LIQ_RATIO  = 50.0   # wolumen/płynność > 50 = podejrzane


def check_sell_pressure(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza czy jest za duża presja sprzedaży.
    """
    buys  = pair.get("buys_1h", 0)
    sells = pair.get("sells_1h", 0)

    if buys == 0 and sells > 0:
        return True, f"Tylko sprzedający w ostatniej godzinie ({sells} sells, 0 buys)"

    if buys > 0 and (sells / buys) > MAX_SELL_RATIO:
        ratio = sells / buys
        return True, f"Wysoka presja sprzedaży: {ratio:.1f}x więcej sells niż buys"

    return False, ""


def check_low_activity(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza czy token ma podejrzanie mało transakcji.
    """
    buys  = pair.get("buys_1h", 0)
    sells = pair.get("sells_1h", 0)
    total = buys + sells

    if total < MIN_TRANSACTIONS_1H:
        return True, f"Bardzo mała aktywność: tylko {total} transakcji w 1h"

    return False, ""


def check_pump_and_dump(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza czy wzrost ceny jest podejrzanie wysoki (pump & dump).
    """
    change_1h = pair.get("change_1h", 0)

    if change_1h > MAX_PRICE_CHANGE_1H:
        return True, f"Podejrzany wzrost ceny: +{change_1h:.0f}% w 1h (możliwy pump & dump)"

    return False, ""


def check_liquidity_trap(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza czy płynność jest za niska — łatwy rugpull.
    """
    liquidity = pair.get("liquidity_usd", 0)

    if liquidity < MIN_LIQUIDITY_LOCKED:
        return True, f"Bardzo niska płynność: ${liquidity:,.0f} (łatwy rugpull)"

    return False, ""


def check_volume_liquidity_ratio(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza stosunek wolumenu do płynności.
    Bardzo wysoki stosunek może oznaczać manipulację wolumenem.
    """
    liquidity  = pair.get("liquidity_usd", 0)
    volume_24h = pair.get("volume_24h", 0)

    if liquidity <= 0:
        return False, ""

    ratio = volume_24h / liquidity

    if ratio > MAX_VOLUME_LIQ_RATIO:
        return True, f"Podejrzany stosunek wolumen/płynność: {ratio:.1f}x"

    return False, ""


def check_no_socials(pair: dict) -> tuple[bool, str]:
    """
    Sprawdza czy token ma jakiekolwiek social media.
    Brak sociali = większe ryzyko rugpull.
    """
    info = pair.get("info") or {}
    socials  = info.get("socials", []) or []
    websites = info.get("websites", []) or []

    if not socials and not websites:
        return True, "Brak social media i strony WWW"

    return False, ""


# ── Główna funkcja ──────────────────────────────────────────────────────────

CHECKS = [
    check_sell_pressure,
    check_low_activity,
    check_pump_and_dump,
    check_liquidity_trap,
    check_volume_liquidity_ratio,
    check_no_socials,
]


def analyze_rugpull_risk(pair: dict) -> dict:
    """
    Analizuje ryzyko rugpull dla danej pary.

    Zwraca dict z:
    - risk_score: 0-100 (im wyższy tym większe ryzyko)
    - risk_level: LOW / MEDIUM / HIGH / CRITICAL
    - warnings: lista ostrzeżeń
    - is_safe: bool czy token jest bezpieczny
    """
    warnings = []

    for check in CHECKS:
        is_risky, reason = check(pair)
        if is_risky:
            warnings.append(reason)

    # Oblicz risk score (każde ostrzeżenie dodaje punkty)
    risk_score = min(len(warnings) * 20, 100)

    if risk_score == 0:
        risk_level = "LOW"
    elif risk_score <= 40:
        risk_level = "MEDIUM"
    elif risk_score <= 60:
        risk_level = "HIGH"
    else:
        risk_level = "CRITICAL"

    is_safe = risk_score <= 40  # akceptujemy max MEDIUM

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