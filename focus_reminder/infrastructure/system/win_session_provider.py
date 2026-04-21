from __future__ import annotations

from focus_reminder.domain.interfaces.session_state_provider import ISessionStateProvider


class WinSessionStateProvider(ISessionStateProvider):
    def is_session_locked(self) -> bool:
        # V1.1: placeholder for future lock screen/session-aware strategy.
        return False

