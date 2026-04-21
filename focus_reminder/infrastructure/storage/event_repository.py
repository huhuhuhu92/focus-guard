from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from focus_reminder.domain.models.reminder_event import ReminderEvent
from focus_reminder.infrastructure.storage.sqlite_manager import SQLiteManager


class ReminderEventRepository:
    def __init__(self, sqlite_manager: SQLiteManager) -> None:
        self._sqlite = sqlite_manager

    def add_event(self, event: ReminderEvent) -> None:
        with self._sqlite.connect() as conn:
            conn.execute(
                """
                INSERT INTO reminder_events (
                    id, level, triggered_at, idle_seconds, media_state, dismiss_mode,
                    trigger_reason, dismiss_reason, popup_duration_ms, foreground_app, foreground_title
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.level.value,
                    event.triggered_at.isoformat(timespec="seconds"),
                    event.idle_seconds,
                    event.media_state.value,
                    event.dismiss_mode.value,
                    event.trigger_reason,
                    event.dismiss_reason,
                    event.popup_duration_ms,
                    event.foreground_app,
                    event.foreground_title,
                ),
            )
            conn.commit()

    def complete_event(
        self,
        event_id: str,
        dismiss_reason: str,
        popup_duration_ms: int,
    ) -> None:
        with self._sqlite.connect() as conn:
            conn.execute(
                """
                UPDATE reminder_events
                SET dismiss_reason = ?, popup_duration_ms = ?
                WHERE id = ?
                """,
                (dismiss_reason, popup_duration_ms, event_id),
            )
            conn.commit()

    def clear_all_events(self) -> None:
        with self._sqlite.connect() as conn:
            conn.execute("DELETE FROM reminder_events")
            conn.commit()

    def get_recent_events(self, limit: int = 100) -> list[dict[str, str | int | None]]:
        with self._sqlite.connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM reminder_events
                ORDER BY triggered_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_today_count(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        return self._count_between(start, end)

    def get_last_n_days_counts(self, days: int = 7, now: Optional[datetime] = None) -> list[tuple[str, int]]:
        now = now or datetime.now()
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        points: list[tuple[str, int]] = []
        for offset in range(days - 1, -1, -1):
            start = day_start - timedelta(days=offset)
            end = start + timedelta(days=1)
            count = self._count_between(start, end)
            points.append((start.strftime("%m-%d"), count))
        return points

    def get_hourly_distribution(self, now: Optional[datetime] = None) -> list[tuple[str, int]]:
        now = now or datetime.now()
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        with self._sqlite.connect() as conn:
            rows = conn.execute(
                """
                SELECT strftime('%H', triggered_at) AS hour_bucket, COUNT(*) AS cnt
                FROM reminder_events
                WHERE triggered_at >= ? AND triggered_at < ?
                GROUP BY hour_bucket
                ORDER BY hour_bucket ASC
                """,
                (
                    start.isoformat(timespec="seconds"),
                    end.isoformat(timespec="seconds"),
                ),
            ).fetchall()

        lookup = {row["hour_bucket"]: row["cnt"] for row in rows}
        result: list[tuple[str, int]] = []
        for hour in range(24):
            key = f"{hour:02d}"
            result.append((key, int(lookup.get(key, 0))))
        return result

    def get_level_distribution(self, days: int = 7, now: Optional[datetime] = None) -> list[tuple[str, int]]:
        start, end = self._range_for_days(days, now)
        with self._sqlite.connect() as conn:
            rows = conn.execute(
                """
                SELECT level AS key, COUNT(*) AS cnt
                FROM reminder_events
                WHERE triggered_at >= ? AND triggered_at < ?
                GROUP BY level
                """,
                (
                    start.isoformat(timespec="seconds"),
                    end.isoformat(timespec="seconds"),
                ),
            ).fetchall()
        counts = {row["key"]: int(row["cnt"]) for row in rows}
        return [
            ("pre_reminder", counts.get("pre_reminder", 0)),
            ("fullscreen_reminder", counts.get("fullscreen_reminder", 0)),
        ]

    def get_dismiss_reason_distribution(
        self,
        days: int = 7,
        now: Optional[datetime] = None,
    ) -> list[tuple[str, int]]:
        start, end = self._range_for_days(days, now)
        with self._sqlite.connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(dismiss_reason), ''), 'pending') AS key, COUNT(*) AS cnt
                FROM reminder_events
                WHERE triggered_at >= ? AND triggered_at < ?
                GROUP BY key
                ORDER BY cnt DESC
                """,
                (
                    start.isoformat(timespec="seconds"),
                    end.isoformat(timespec="seconds"),
                ),
            ).fetchall()
        return [(str(row["key"]), int(row["cnt"])) for row in rows]

    def get_trigger_reason_distribution(
        self,
        days: int = 7,
        now: Optional[datetime] = None,
    ) -> list[tuple[str, int]]:
        start, end = self._range_for_days(days, now)
        with self._sqlite.connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(NULLIF(TRIM(trigger_reason), ''), 'unknown') AS key, COUNT(*) AS cnt
                FROM reminder_events
                WHERE triggered_at >= ? AND triggered_at < ?
                GROUP BY key
                ORDER BY cnt DESC
                """,
                (
                    start.isoformat(timespec="seconds"),
                    end.isoformat(timespec="seconds"),
                ),
            ).fetchall()
        return [(str(row["key"]), int(row["cnt"])) for row in rows]

    def _count_between(self, start: datetime, end: datetime) -> int:
        with self._sqlite.connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*) AS cnt
                FROM reminder_events
                WHERE triggered_at >= ? AND triggered_at < ?
                """,
                (
                    start.isoformat(timespec="seconds"),
                    end.isoformat(timespec="seconds"),
                ),
            ).fetchone()
        return int(row["cnt"]) if row else 0

    def _range_for_days(self, days: int, now: Optional[datetime]) -> tuple[datetime, datetime]:
        now = now or datetime.now()
        safe_days = max(1, int(days))
        end = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        start = end - timedelta(days=safe_days)
        return start, end
