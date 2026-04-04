import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_PATH = Path(__file__).parent.parent / "config.yml"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        logger.error(f"Brak pliku konfiguracyjnego: {CONFIG_PATH}")
        raise FileNotFoundError(f"Nie znaleziono config.yml w {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    logger.info(f"Wczytano konfigurację z {CONFIG_PATH}")
    return config

config = load_config()