from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from focus_reminder.domain.enums.media_state import MediaState
from focus_reminder.domain.interfaces.media_state_provider import IMediaStateProvider
from focus_reminder.domain.interfaces.window_state_provider import IWindowStateProvider


@dataclass(frozen=True, slots=True)
class MediaHeuristicConfig:
    browser_processes: frozenset[str] = frozenset(
        {
            "chrome.exe",
            "msedge.exe",
            "firefox.exe",
            "opera.exe",
            "brave.exe",
            "360chrome.exe",
            "qqbrowser.exe",
        }
    )
    video_processes: frozenset[str] = frozenset(
        {
            "vlc.exe",
            "potplayermini64.exe",
            "potplayermini.exe",
            "mpv.exe",
            "kodi.exe",
            "youku.exe",
            "qqlive.exe",
            "iqiyi.exe",
            "bilibili.exe",
        }
    )
    audio_processes: frozenset[str] = frozenset(
        {
            "spotify.exe",
            "cloudmusic.exe",
            "qqmusic.exe",
            "kugou.exe",
            "music.ui.exe",
        }
    )
    video_title_keywords: tuple[str, ...] = (
        "youtube",
        "bilibili",
        "netflix",
        "twitch",
        "youku",
        "iqiyi",
        "qqlive",
        "video",
        "影片",
        "电影",
        "剧集",
        "直播",
        "播放",
    )
    audio_title_keywords: tuple[str, ...] = (
        "spotify",
        "music",
        "podcast",
        "歌曲",
        "专辑",
        "电台",
        "听歌",
    )


class HeuristicMediaStateProvider(IMediaStateProvider):
    def __init__(
        self,
        window_state_provider: IWindowStateProvider,
        config: MediaHeuristicConfig | None = None,
    ) -> None:
        self._window_state_provider = window_state_provider
        self._config = config or MediaHeuristicConfig()

    def get_media_state(self) -> MediaState:
        try:
            process_name = self._normalize(self._window_state_provider.get_foreground_process_name())
            title = self._normalize(self._window_state_provider.get_foreground_window_title())

            if not process_name and not title:
                return MediaState.NONE

            if process_name in self._config.video_processes:
                return MediaState.VIDEO_PLAYING

            if process_name in self._config.audio_processes:
                return MediaState.AUDIO_ONLY

            if process_name in self._config.browser_processes:
                if self._contains_any(title, self._config.video_title_keywords):
                    return MediaState.VIDEO_PLAYING
                if self._contains_any(title, self._config.audio_title_keywords):
                    return MediaState.AUDIO_ONLY
                if title:
                    return MediaState.UNKNOWN
                return MediaState.NONE

            if self._contains_any(title, self._config.video_title_keywords):
                return MediaState.VIDEO_PLAYING
            if self._contains_any(title, self._config.audio_title_keywords):
                return MediaState.AUDIO_ONLY
            return MediaState.NONE
        except Exception:
            return MediaState.UNKNOWN

    def _contains_any(self, text: str, keywords: Iterable[str]) -> bool:
        if not text:
            return False
        return any(keyword in text for keyword in keywords)

    def _normalize(self, value: str | None) -> str:
        return (value or "").strip().lower()

