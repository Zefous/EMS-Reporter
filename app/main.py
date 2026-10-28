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
    app = QApplication(sys.argv)
    app.setApplicationName("EMS Reporter")
    app.setOrganizationName("Majestic RP EMS")
    app.setStyleSheet(MEDICAL_QSS)

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
