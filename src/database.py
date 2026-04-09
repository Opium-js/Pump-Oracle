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


def save_tokens(scan_id: int, tokens: list[dict]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.executemany(
            """INSERT INTO tokens (
                scan_id, found_at, name, pair_address, dex,
                price_usd, liquidity, volume_24h, volume_1h,
                change_1h, change_24h, age_hours,
                risk_level, risk_score, url, tags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(
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
            ) for t in tokens]
        )
    logger.info(f"Zapisano {len(tokens)} tokenów do bazy (scan_id: {scan_id})")


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
    """
    Pobiera statystyki wszystkich skanów.
    """
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