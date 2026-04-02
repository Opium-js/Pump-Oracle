import os
import time
import logging
from dotenv import load_dotenv

from src.data.fetcher import get_new_solana_pairs
from src.analyzers.onchain import analyze_pairs, get_interesting_pairs

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

SCAN_INTERVAL_MINUTES = 15


def run_scan() -> None:
    logger.info("━" * 50)
    logger.info("Rozpoczynam skan...")

    # 1. Pobierz dane
    raw_pairs = get_new_solana_pairs()
    if not raw_pairs:
        logger.warning("Brak danych z API — przerywam skan")
        return

    # 2. Analizuj
    df = analyze_pairs(raw_pairs)
    interesting = get_interesting_pairs(raw_pairs)

    logger.info(f"Skan zakończony: {len(interesting)}/{len(df)} ciekawych par")

    # 3. Wyświetl w terminalu
    for pair in interesting:
        age_str = f"{pair['age_hours']:.1f}h" if pair['age_hours'] else "?"
        logger.info(
            f"{ pair['name']:<20} "
            f"vol: ${pair['volume_24h']:>10,.0f} | "
            f"liq: ${pair['liquidity_usd']:>8,.0f} | "
            f"1h: {pair['change_1h']:>+6.1f}% | "
            f"wiek: {age_str}"
        )

    # 4. Powiadomienia Telegram (gdy będzie skonfigurowany)
    token   = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        from src.notifiers.telegram import notify_interesting_pairs
        notify_interesting_pairs(token, chat_id, interesting, len(df))
    else:
        logger.info(" Telegram niezskonfigurowany — pomijam powiadomienia")


def main() -> None:
    logger.info("Pump-Oracle uruchomiony!")
    logger.info(f" Skan co {SCAN_INTERVAL_MINUTES} minut")

    while True:
        try:
            run_scan()
        except Exception as e:
            logger.error(f"Nieoczekiwany błąd: {e}", exc_info=True)

        logger.info(f"Następny skan za {SCAN_INTERVAL_MINUTES} min...")
        time.sleep(SCAN_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()