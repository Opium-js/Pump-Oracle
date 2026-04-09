import logging
import requests
from src.analyzers.categorizer import format_tags
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def send_message(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text":    text,
            "disable_web_page_preview": True,
        }, timeout=10)
        response.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        logger.error(f"Błąd wysyłania na Telegram: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Odpowiedź Telegrama: {e.response.text}")
        return False


def format_pair_message(pair: dict) -> str:
    age = pair.get("age_hours")
    age_str = f"{age:.1f}h" if age is not None else "?"

    change_1h  = pair.get("change_1h", 0)
    change_24h = pair.get("change_24h", 0)
    change_1h_icon  = "🟢" if change_1h  >= 0 else "🔴"
    change_24h_icon = "🟢" if change_24h >= 0 else "🔴"

    ratio = pair.get("buy_sell_ratio", 0)
    ratio_str = f"{ratio:.2f}" if ratio != float("inf") else "inf"

    return (
        f"🚀 {pair['name']} — {pair['dex'].upper()}\n"
        f"{format_tags(pair.get('tags', []))}\n"
        f"\n"
        f"💧 Płynność:    ${pair['liquidity_usd']:,.0f}\n"
        f"📊 Wolumen 24h: ${pair['volume_24h']:,.0f}\n"
        f"📊 Wolumen 1h:  ${pair['volume_1h']:,.0f}\n"
        f"\n"
        f"{change_1h_icon} Zmiana 1h:  {change_1h:+.1f}%\n"
        f"{change_24h_icon} Zmiana 24h: {change_24h:+.1f}%\n"
        f"\n"
        f"🔄 Buy/Sell 1h: {ratio_str}\n"
        f"⏱️ Wiek pary:   {age_str}\n"
        f"\n"
        f"🛡️ Ryzyko:      {pair.get('risk_level', 'N/A')} "
        f"(score: {pair.get('risk_score', 'N/A')})\n"
        f"\n"
        f"🔗 {pair['url']}"
    )


def format_summary_message(count: int, total: int) -> str:
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    return (
        f"🔍 Skan zakończony — {now}\n"
        f"Przeanalizowano {total} par\n"
        f"Znaleziono {count} ciekawych tokenów"
    )


def notify_interesting_pairs(
    token: str,
    chat_id: str,
    pairs: list[dict],
    total_scanned: int,
) -> None:
    if not pairs:
        summary = format_summary_message(0, total_scanned)
        send_message(token, chat_id, summary)
        return

    summary = format_summary_message(len(pairs), total_scanned)
    send_message(token, chat_id, summary)

    for pair in pairs:
        msg = format_pair_message(pair)
        send_message(token, chat_id, msg)
        logger.info(f"Wysłano powiadomienie: {pair['name']}")