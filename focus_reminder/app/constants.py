from __future__ import annotations

from pathlib import Path

APP_NAME = "Focus Reminder Desktop"
APP_VERSION = "1.1.0"

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
RESOURCE_DIR = BASE_DIR / "resources"
ICON_DIR = RESOURCE_DIR / "icons"

CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "focus_reminder.db"

