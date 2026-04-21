from __future__ import annotations

import unittest

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.interfaces.window_state_provider import IWindowStateProvider
from focus_reminder.infrastructure.system.media_provider_heuristic import (
    HeuristicMediaStateProvider,
)


class FakeWindowStateProvider(IWindowStateProvider):
    def __init__(self, process_name: str | None, window_title: str | None) -> None:
        self._process_name = process_name
        self._window_title = window_title

    def get_foreground_process_name(self) -> str | None:
        return self._process_name

    def get_foreground_window_title(self) -> str | None:
        return self._window_title


class HeuristicMediaStateProviderTests(unittest.TestCase):
    def test_known_video_process_returns_video_playing(self) -> None:
        provider = HeuristicMediaStateProvider(
            FakeWindowStateProvider("vlc.exe", "Some Video")
        )
        self.assertEqual(provider.get_media_state(), MediaState.VIDEO_PLAYING)

    def test_known_audio_process_returns_audio_only(self) -> None:
        provider = HeuristicMediaStateProvider(
            FakeWindowStateProvider("spotify.exe", "Now Playing")
        )
        self.assertEqual(provider.get_media_state(), MediaState.AUDIO_ONLY)

    def test_browser_video_keyword_returns_video_playing(self) -> None:
        provider = HeuristicMediaStateProvider(
            FakeWindowStateProvider("msedge.exe", "YouTube - Study Session")
        )
        self.assertEqual(provider.get_media_state(), MediaState.VIDEO_PLAYING)

    def test_browser_unknown_title_returns_unknown(self) -> None:
        provider = HeuristicMediaStateProvider(
            FakeWindowStateProvider("chrome.exe", "Some Article Page")
        )
        self.assertEqual(provider.get_media_state(), MediaState.UNKNOWN)

    def test_no_process_no_title_returns_none(self) -> None:
        provider = HeuristicMediaStateProvider(
            FakeWindowStateProvider(None, None)
        )
        self.assertEqual(provider.get_media_state(), MediaState.NONE)


if __name__ == "__main__":
    unittest.main()

