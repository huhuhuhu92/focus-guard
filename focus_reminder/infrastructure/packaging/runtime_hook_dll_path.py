from __future__ import annotations

import os
import sys
from pathlib import Path


def _add_dll_search_path(path: Path) -> None:
    if not path.exists():
        return
    try:
        os.add_dll_directory(str(path))
    except (AttributeError, OSError):
        pass


def _prepend_path(path: Path) -> None:
    if not path.exists():
        return
    current = os.environ.get("PATH", "")
    parts = current.split(os.pathsep) if current else []
    value = str(path)
    if value not in parts:
        os.environ["PATH"] = value + (os.pathsep + current if current else "")


def _configure_runtime_dll_paths() -> None:
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        exe_dir = Path(sys.executable).resolve().parent
    else:
        return

    candidates = [
        exe_dir,
        exe_dir / "_internal",
        exe_dir / "PySide6",
        exe_dir / "shiboken6",
        exe_dir / "_internal" / "PySide6",
        exe_dir / "_internal" / "shiboken6",
        exe_dir / "_internal" / "PySide6" / "plugins",
        exe_dir / "_internal" / "PySide6" / "plugins" / "platforms",
        bundle_root,
        bundle_root / "PySide6",
        bundle_root / "shiboken6",
        bundle_root / "PySide6" / "plugins",
        bundle_root / "PySide6" / "plugins" / "platforms",
    ]

    for path in candidates:
        _add_dll_search_path(path)
        _prepend_path(path)


_configure_runtime_dll_paths()
