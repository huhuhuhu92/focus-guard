from __future__ import annotations

import sqlite3
from pathlib import Path


class SQLiteManager:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    @property
    def db_path(self) -> Path:
        return self._db_path

    def initialize(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS reminder_events (
                    id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    triggered_at TEXT NOT NULL,
                    idle_seconds INTEGER NOT NULL,
                    media_state TEXT NOT NULL,
                    dismiss_mode TEXT NOT NULL,
                    trigger_reason TEXT,
                    dismiss_reason TEXT,
                    popup_duration_ms INTEGER,
                    foreground_app TEXT,
                    foreground_title TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            self._ensure_column(conn, "reminder_events", "trigger_reason", "TEXT")
            conn.commit()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
        ddl_type: str,
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        existing = {row["name"] for row in rows}
        if column in existing:
            return
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")
