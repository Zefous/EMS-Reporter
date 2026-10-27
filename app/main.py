"""Application entry point for EMS Reporter."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.theme import MEDICAL_QSS
from app.main_window import MainWindow


def main():
    """Main startup procedure."""
    app = QApplication(sys.argv)
    app.setApplicationName("EMS Reporter")
    app.setOrganizationName("Majestic RP EMS")
    app.setStyleSheet(MEDICAL_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
