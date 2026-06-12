"""Shared SQLite dedup tracker for signal scrapers.

Mirrors the seen-tracker pattern in signals/h1b_signal_engine.py, but
parameterized by table name so multiple scrapers can share database/tracker.db
without re-spamming the same leads on repeated runs.

    t = SeenTracker("ttb_leads_seen")
    if not t.is_seen(key):
        ...route lead...
        t.mark_seen(key)
"""
import sqlite3
from datetime import datetime
from pathlib import Path

_DEFAULT_DB = Path(__file__).resolve().parent.parent / "database" / "tracker.db"


class SeenTracker:
    def __init__(self, table: str, db_path=None):
        # table is interpolated into DDL, so restrict to identifier chars.
        if not table.replace("_", "").isalnum():
            raise ValueError(f"Invalid table name: {table!r}")
        self.table = table
        self.db_path = Path(db_path) if db_path else _DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as conn:
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dedup_key TEXT UNIQUE,
                    scraped_at TEXT
                )
                """
            )

    def _conn(self):
        return sqlite3.connect(str(self.db_path))

    def is_seen(self, dedup_key: str) -> bool:
        with self._conn() as conn:
            row = conn.execute(
                f"SELECT 1 FROM {self.table} WHERE dedup_key=?", (dedup_key,)
            ).fetchone()
        return row is not None

    def mark_seen(self, dedup_key: str) -> None:
        try:
            with self._conn() as conn:
                conn.execute(
                    f"INSERT INTO {self.table} (dedup_key, scraped_at) VALUES (?,?)",
                    (dedup_key, datetime.utcnow().isoformat()),
                )
        except sqlite3.IntegrityError:
            pass
