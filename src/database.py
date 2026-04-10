import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "pump_oracle.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # wyniki jako dict
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scans (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scanned_at  TEXT NOT NULL,
                total_pairs INTEGER NOT NULL,
                found_pairs INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS tokens (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id      INTEGER NOT NULL,
                found_at     TEXT NOT NULL,
                name         TEXT NOT NULL,
                pair_address TEXT NOT NULL,
                dex          TEXT NOT NULL,
                price_usd    REAL,
                liquidity    REAL,
                volume_24h   REAL,
                volume_1h    REAL,
                change_1h    REAL,
                change_24h   REAL,
                age_hours    REAL,
                risk_level   TEXT,
                risk_score   INTEGER,
                url          TEXT,
                tags         TEXT,
                FOREIGN KEY (scan_id) REFERENCES scans(id)
            );
                           
            CREATE TABLE IF NOT EXISTS token_tracking (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id        INTEGER NOT NULL,
                pair_address    TEXT NOT NULL,
                name            TEXT NOT NULL,
                price_at_found  REAL NOT NULL,
                price_1h        REAL,
                price_6h        REAL,
                price_24h       REAL,
                change_1h       REAL,
                change_6h       REAL,
                change_24h      REAL,
                found_at        TEXT NOT NULL,
                checked_1h_at   TEXT,
                checked_6h_at   TEXT,
                checked_24h_at  TEXT,
                FOREIGN KEY (token_id) REFERENCES tokens(id)
            );
        """)
    logger.info(f"Baza danych zainicjalizowana: {DB_PATH}")


def save_scan(total_pairs: int, found_pairs: int) -> int:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO scans (scanned_at, total_pairs, found_pairs) VALUES (?, ?, ?)",
            (now, total_pairs, found_pairs)
        )
        return cursor.lastrowid


def save_tokens(scan_id: int, tokens: list[dict]) -> list[int]:
    now = datetime.now(timezone.utc).isoformat()
    token_ids = []
    with get_connection() as conn:
        for t in tokens:
            cursor = conn.execute(
                """INSERT INTO tokens (
                    scan_id, found_at, name, pair_address, dex,
                    price_usd, liquidity, volume_24h, volume_1h,
                    change_1h, change_24h, age_hours,
                    risk_level, risk_score, url, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    scan_id,
                    now,
                    t.get("name", ""),
                    t.get("pair_address", ""),
                    t.get("dex", ""),
                    t.get("price_usd", 0),
                    t.get("liquidity_usd", 0),
                    t.get("volume_24h", 0),
                    t.get("volume_1h", 0),
                    t.get("change_1h", 0),
                    t.get("change_24h", 0),
                    t.get("age_hours"),
                    t.get("risk_level", "N/A"),
                    t.get("risk_score", 0),
                    t.get("url", ""),
                    ",".join(t.get("tags", [])),
                )
            )
            token_ids.append(cursor.lastrowid)
    logger.info(f"Zapisano {len(tokens)} tokenów do bazy (scan_id: {scan_id})")
    return token_ids


def get_recent_tokens(limit: int = 50) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT t.*, s.scanned_at 
               FROM tokens t
               JOIN scans s ON t.scan_id = s.id
               ORDER BY t.found_at DESC
               LIMIT ?""",
            (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def get_scan_stats() -> dict:
    with get_connection() as conn:
        stats = conn.execute("""
            SELECT 
                COUNT(*)           as total_scans,
                SUM(total_pairs)   as total_pairs_analyzed,
                SUM(found_pairs)   as total_tokens_found,
                MAX(scanned_at)    as last_scan
            FROM scans
        """).fetchone()
    return dict(stats)

def save_token_for_tracking(token_id: int, pair: dict) -> None:
    found_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO token_tracking 
               (token_id, pair_address, name, price_at_found, found_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                token_id,
                pair.get("pair_address", ""),
                pair.get("name", ""),
                pair.get("price_usd", 0),
                found_at,
            )
        )
    logger.info(f"Dodano {pair.get('name')} do trackingu (cena: ${pair.get('price_usd', 0):.6f})")


def get_tokens_to_check() -> list[dict]:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT * FROM token_tracking
               WHERE (checked_1h_at  IS NULL AND substr(found_at, 1, 19) <= datetime(?, '-1 hours'))
                  OR (checked_6h_at  IS NULL AND substr(found_at, 1, 19) <= datetime(?, '-6 hours'))
                  OR (checked_24h_at IS NULL AND substr(found_at, 1, 19) <= datetime(?, '-24 hours'))""",
            (now, now, now)
        ).fetchall()
    return [dict(row) for row in rows]


def update_token_price(
    tracking_id: int,
    interval: str,
    current_price: float,
    price_at_found: float,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    change = ((current_price - price_at_found) / price_at_found * 100) if price_at_found > 0 else 0

    with get_connection() as conn:
        conn.execute(
            f"""UPDATE token_tracking SET
                price_{interval}       = ?,
                change_{interval}      = ?,
                checked_{interval}_at  = ?
                WHERE id = ?""",
            (current_price, change, now, tracking_id)
        )
    logger.info(f"Zaktualizowano cenę {interval}: {change:+.1f}%")