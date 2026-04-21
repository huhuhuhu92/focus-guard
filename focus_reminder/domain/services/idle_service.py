from __future__ import annotations


class IdleService:
    def get_idle_seconds(self, last_active_time: float, now_monotonic: float) -> int:
        return max(0, int(now_monotonic - last_active_time))

