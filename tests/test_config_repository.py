from __future__ import annotations

import shutil
import unittest
import uuid
from pathlib import Path

from focus_reminder.domain.enums.dismiss_mode import DismissMode
from focus_reminder.domain.models.config import FocusConfig
from focus_reminder.infrastructure.storage.config_repository import ConfigRepository


class ConfigRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        base = Path("tests/.tmp")
        base.mkdir(parents=True, exist_ok=True)
        self._workdir = base / str(uuid.uuid4())
        self._workdir.mkdir(parents=True, exist_ok=True)

    def tearDown(self) -> None:
        shutil.rmtree(self._workdir, ignore_errors=True)

    def test_round_trip(self) -> None:
        repo = ConfigRepository(self._workdir / "config.json")
        config = FocusConfig(
            idle_threshold_seconds=420,
            pre_reminder_seconds=80,
            dismiss_mode=DismissMode.MANUAL,
        )
        repo.save(config)
        loaded = repo.load()
        self.assertEqual(loaded.idle_threshold_seconds, 420)
        self.assertEqual(loaded.pre_reminder_seconds, 80)
        self.assertEqual(loaded.dismiss_mode, DismissMode.MANUAL)

    def test_fallback_when_corrupted(self) -> None:
        path = self._workdir / "config.json"
        path.write_text("{broken", encoding="utf-8")
        repo = ConfigRepository(path)
        loaded = repo.load()
        self.assertIsInstance(loaded, FocusConfig)
        self.assertGreater(loaded.idle_threshold_seconds, 0)


if __name__ == "__main__":
    unittest.main()
