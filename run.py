#!/usr/bin/env python3
"""Cross-platform runner script for EMS Reporter (Majestic GTA V RP)."""

import os
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Auto-switch to .venv python if running from source (not frozen in .exe)
if not getattr(sys, "frozen", False):
    venv_windows = (project_root / ".venv" / "Scripts" / "python.exe").resolve()
    venv_unix = (project_root / ".venv" / "bin" / "python3").resolve()
    current_exe = Path(sys.executable).resolve()

    if venv_windows.is_file() and current_exe != venv_windows:
        sys.exit(subprocess.call([str(venv_windows), str(project_root / "run.py")] + sys.argv[1:]))
    elif venv_unix.is_file() and current_exe != venv_unix:
        sys.exit(subprocess.call([str(venv_unix), str(project_root / "run.py")] + sys.argv[1:]))

# Verify dependencies
missing = []
for pkg in ["PySide6", "pydantic"]:
    try:
        __import__(pkg)
    except ImportError:
        missing.append(pkg)

if missing:
    print(f"[ERROR] Отсутствуют необходимые библиотеки: {', '.join(missing)}")
    print("[INFO] Установите зависимости командой:")
    print("       pip install -r requirements.txt")
    print("\nЛибо запустите run.bat (на Windows) для автоматической настройки.")
    try:
        input("\nНажмите Enter для выхода...")
    except Exception:
        pass
    sys.exit(1)

from app.main import main

if __name__ == "__main__":
    main()
