from __future__ import annotations

from enum import Enum


class MediaState(str, Enum):
    NONE = "none"
    AUDIO_ONLY = "audio_only"
    VIDEO_PLAYING = "video_playing"
    UNKNOWN = "unknown"

