import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent / "data" / "pump_oracle.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_completed_tracks() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT t.name, t.tags, t.risk_level, t.risk_score,
                      tr.price_at_found, tr.price_1h, tr.price_6h, tr.price_24h,
                      tr.change_1h, tr.change_6h, tr.change_24h,
                      tr.found_at
               FROM token_tracking tr
               JOIN tokens t ON tr.token_id = t.id
               WHERE tr.price_1h IS NOT NULL"""
        ).fetchall()
    return [dict(row) for row in rows]


def calculate_stats(changes: list[float]) -> dict:
    if not changes:
        return {"count": 0, "win_rate": 0, "avg_change": 0, "best": 0, "worst": 0}

    wins = [c for c in changes if c > 0]
    return {
        "count":      len(changes),
        "win_rate":   len(wins) / len(changes) * 100,
        "avg_change": sum(changes) / len(changes),
        "best":       max(changes),
        "worst":      min(changes),
    }


def run_backtest() -> dict:
    tracks = get_completed_tracks()

    if not tracks:
        logger.warning("Brak danych do backtestingu — poczekaj na więcej skanów")
        return {}

    logger.info(f"Analizuję {len(tracks)} tokenów...")

    changes_1h  = [t["change_1h"]  for t in tracks if t["change_1h"]  is not None]
    changes_6h  = [t["change_6h"]  for t in tracks if t["change_6h"]  is not None]
    changes_24h = [t["change_24h"] for t in tracks if t["change_24h"] is not None]

    stats_1h  = calculate_stats(changes_1h)
    stats_6h  = calculate_stats(changes_6h)
    stats_24h = calculate_stats(changes_24h)

    risk_stats = {}
    for level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        level_changes = [
            t["change_1h"] for t in tracks
            if t["risk_level"] == level and t["change_1h"] is not None
        ]
        risk_stats[level] = calculate_stats(level_changes)

    tag_stats = {}
    all_tags = ["nowy", "gorący", "ryzykowny", "wieloryb", "mikro"]
    for tag in all_tags:
        tag_changes = [
            t["change_1h"] for t in tracks
            if t["tags"] and tag in t["tags"] and t["change_1h"] is not None
        ]
        if tag_changes:
            tag_stats[tag] = calculate_stats(tag_changes)

    return {
        "total_tokens":  len(tracks),
        "stats_1h":      stats_1h,
        "stats_6h":      stats_6h,
        "stats_24h":     stats_24h,
        "by_risk":       risk_stats,
        "by_tag":        tag_stats,
        "tokens":        tracks,
    }


def print_report(results: dict) -> None:
    if not results:
        print("Brak danych do wyświetlenia")
        return

    print("\n" + "═" * 55)
    print("📊  PUMP-ORACLE — RAPORT BACKTESTINGU")
    print("═" * 55)
    print(f"Przeanalizowano tokenów: {results['total_tokens']}")

    for label, stats in [("1h", results["stats_1h"]), ("6h", results["stats_6h"]), ("24h", results["stats_24h"])]:
        if stats["count"] == 0:
            continue
        print(f"\n⏱️  Wyniki po {label} ({stats['count']} tokenów):")
        print(f"   Win rate:      {stats['win_rate']:.1f}%")
        print(f"   Średnia zmiana:{stats['avg_change']:+.1f}%")
        print(f"   Najlepszy:     {stats['best']:+.1f}%")
        print(f"   Najgorszy:     {stats['worst']:+.1f}%")

    print("\n🛡️  Skuteczność wg poziomu ryzyka (1h):")
    for level, stats in results["by_risk"].items():
        if stats["count"] == 0:
            continue
        print(f"   {level:<10} win rate: {stats['win_rate']:.1f}% | avg: {stats['avg_change']:+.1f}% | n={stats['count']}")

    if results["by_tag"]:
        print("\n🏷️  Skuteczność wg tagów (1h):")
        for tag, stats in results["by_tag"].items():
            print(f"   {tag:<12} win rate: {stats['win_rate']:.1f}% | avg: {stats['avg_change']:+.1f}% | n={stats['count']}")

    tokens = sorted(results["tokens"], key=lambda x: x["change_1h"] or 0, reverse=True)
    print("\n🚀  Top 3 tokeny (1h):")
    for t in tokens[:3]:
        print(f"   {t['name']:<20} {t['change_1h']:+.1f}%  [{t['risk_level']}]")

    print("\n💀  Worst 3 tokeny (1h):")
    for t in tokens[-3:]:
        print(f"   {t['name']:<20} {t['change_1h']:+.1f}%  [{t['risk_level']}]")

    print("\n" + "═" * 55)


if __name__ == "__main__":
    results = run_backtest()
    print_report(results)