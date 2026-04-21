from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "Focus Reminder Desktop"
APP_VERSION = "1.3.0"

PACKAGE_DIR = Path(__file__).resolve().parents[1]

if getattr(sys, "frozen", False):
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    RESOURCE_DIR = BUNDLE_DIR / "focus_reminder" / "resources"
    data_root = Path(os.environ.get("APPDATA", str(Path.home()))) / "FocusReminderDesktop"
else:
    RESOURCE_DIR = PACKAGE_DIR / "resources"
    data_root = PACKAGE_DIR / "data"

DATA_DIR = data_root
ICON_DIR = RESOURCE_DIR / "icons"

CONFIG_PATH = DATA_DIR / "config.json"
DB_PATH = DATA_DIR / "focus_reminder.db"
