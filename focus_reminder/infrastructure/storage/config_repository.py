from __future__ import annotations

import json
from pathlib import Path

from focus_reminder.domain.models.config import FocusConfig


class ConfigRepository:
    def __init__(self, config_path: Path) -> None:
        self._config_path = config_path

    def load(self) -> FocusConfig:
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._config_path.exists():
            config = FocusConfig().sanitized()
            self.save(config)
            return config

        try:
            with self._config_path.open("r", encoding="utf-8") as file:
                raw = json.load(file)
        except (json.JSONDecodeError, OSError, TypeError, ValueError):
            config = FocusConfig().sanitized()
            self.save(config)
            return config

        return FocusConfig.from_dict(raw)

    def save(self, config: FocusConfig) -> None:
        cfg = config.sanitized()
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with self._config_path.open("w", encoding="utf-8") as file:
            json.dump(cfg.to_dict(), file, ensure_ascii=False, indent=2)

