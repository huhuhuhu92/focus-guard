from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from focus_reminder.app.bootstrap import AppBootstrap
from focus_reminder.app.constants import APP_NAME


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def main() -> int:
    setup_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)

    bootstrap = AppBootstrap(app)
    bootstrap.start()
    app.aboutToQuit.connect(bootstrap.shutdown)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

