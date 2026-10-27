"""Script to generate a full visual preview of EMS Reporter."""

import os
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.report_dialog import ReportPreviewDialog
from app.theme import MEDICAL_QSS
from app.models import FieldType


def create_demo_screenshot():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(MEDICAL_QSS)

    # Create temporary folders with dummy screenshots
    demo_dir = Path("/home/burmalda/Кирилл/EMS reporter/temp_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    demo_dir.mkdir(parents=True)

    day_city = demo_dir / "ПМП день (Город)"
    day_city.mkdir()
    for i in range(13):
        (day_city / f"screen_day_{i:02d}.png").write_text("dummy")

    night_city = demo_dir / "ПМП ночь (Город)"
    night_city.mkdir()
    for i in range(7):
        (night_city / f"screen_night_{i:02d}.png").write_text("dummy")

    pills = demo_dir / "Выдача таблеток"
    pills.mkdir()
    for i in range(25):
        (pills / f"pills_{i:02d}.jpg").write_text("dummy")

    # Initialize MainWindow with demo config
    demo_cfg = demo_dir / "demo_config.json"
    win = MainWindow(config_path=str(demo_cfg))
    win.name_edit.setText("Kirill Alvarez")
    win.static_edit.setText("#18290")
    win.rank_edit.setText("Paramedic Special")

    # Set paths in PM tab
    pm_tab = win.config.tabs[0]
    pm_tab.fields[0].folder_path = str(day_city)      # 13 * 2 = 26 pts
    pm_tab.fields[1].folder_path = str(night_city)    # 7 * 3 = 21 pts
    pm_tab.fields[4].folder_path = str(pills)         # 25 * 1 = 25 pts

    # Numeric fields
    pm_tab.fields[8].manual_count = 2   # Участие в мероприятии (2 * 5 = 10 pts)
    pm_tab.fields[9].manual_count = 1   # Счастливый вызов (1 * 10 = 10 pts)
    pm_tab.fields[10].manual_count = 4  # Мед. справки (4 * 5 = 20 pts)

    win.rebuild_tabs()
    win.force_refresh_all()

    win.resize(1200, 780)
    win.show()

    # Process events to allow layout
    app.processEvents()

    screenshot_path = "/home/burmalda/Кирилл/EMS reporter/preview.png"
    pix = win.grab()
    pix.save(screenshot_path)
    print(f"Preview saved to {screenshot_path}")

    # Also render ReportPreviewDialog
    dlg = MainWindow.open_report_dialog
    report_dlg = ReportPreviewDialog(win.config, current_tab_id=win.config.active_tab_id)
    report_dlg.resize(750, 620)
    report_dlg.show()
    app.processEvents()

    report_pix = report_dlg.grab()
    report_path = "/home/burmalda/Кирилл/EMS reporter/report_preview.png"
    report_pix.save(report_path)
    print(f"Report preview saved to {report_path}")
    report_dlg.close()

    # Cleanup demo dir
    shutil.rmtree(demo_dir, ignore_errors=True)
    win.close()


if __name__ == "__main__":
    create_demo_screenshot()
