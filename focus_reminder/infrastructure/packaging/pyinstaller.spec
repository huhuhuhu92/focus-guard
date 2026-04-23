# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs

project_root = Path(SPECPATH).resolve().parents[2]
main_script = project_root / "focus_reminder" / "app" / "main.py"

block_cipher = None

qt_binaries = collect_dynamic_libs("PySide6")
shiboken_binaries = collect_dynamic_libs("shiboken6")
qt_datas = collect_data_files("PySide6", include_py_files=False)

a = Analysis(
    [str(main_script)],
    pathex=[str(project_root)],
    binaries=qt_binaries + shiboken_binaries,
    datas=[
        (str(project_root / "focus_reminder" / "resources"), "focus_reminder/resources"),
        (str(project_root / "focus_reminder" / "data" / "config.json"), "focus_reminder/data"),
    ] + qt_datas,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    name="FocusReminderDesktop",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    exclude_binaries=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FocusReminderDesktop",
)
