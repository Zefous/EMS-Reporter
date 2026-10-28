"""Application entry point for EMS Reporter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.theme import MEDICAL_QSS
from app.main_window import MainWindow


def main():
    """Main startup procedure."""
    # Windows Per-Monitor High-DPI Awareness (prevents window overflow and blurry scaling)
    if sys.platform == "win32":
        try:
            import ctypes
            # 2 = PROCESS_PER_MONITOR_DPI_AWARE_V2
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                import ctypes
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

    app = QApplication(sys.argv)
    app.setApplicationName("EMS Reporter")
    app.setOrganizationName("Majestic RP EMS")
    app.setStyleSheet(MEDICAL_QSS)

    # Resolve bundle directory for icons (works both in development and PyInstaller .exe)
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).resolve().parent.parent

    for icon_name in ["icon.ico", "icon.png"]:
        icon_file = base_dir / icon_name
        if icon_file.is_file():
            app.setWindowIcon(QIcon(str(icon_file)))
            break

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
