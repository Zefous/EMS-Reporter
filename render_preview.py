"""Script to generate a full visual preview of EMS Reporter with updated requirements."""

import os
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.report_dialog import ReportPreviewDialog
from app.theme import MEDICAL_QSS
from app.models import ReportField, FieldType


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
    for i in range(10):
        (day_city / f"screen_day_{i:02d}.png").write_text("dummy")

    night_city = demo_dir / "ПМП ночь (Город)"
    night_city.mkdir()
    for i in range(6):
        (night_city / f"screen_night_{i:02d}.png").write_text("dummy")

    # Initialize MainWindow with demo config
    demo_cfg = demo_dir / "demo_config.json"
    win = MainWindow(config_path=str(demo_cfg))
    win.name_edit.setText("Jason Mitsui")
    win.static_edit.setText("206277")
    win.rank_edit.setText("Paramedic")

    # Add demo fields to PM tab (simulating user-created fields)
    pm_tab = win.config.tabs[0]
    pm_tab.fields = [
        ReportField(
            id="fld-1",
            name="ПМП день (Город)",
            field_type=FieldType.FOLDER,
            folder_path=str(day_city),
            points_per_unit=2.0,
            cloud_link="https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoP"
        ),
        ReportField(
            id="fld-2",
            name="ПМП ночь (Город)",
            field_type=FieldType.FOLDER,
            folder_path=str(night_city),
            points_per_unit=3.0,
            cloud_link=""  # No cloud link
        ),
        ReportField(
            id="fld-3",
            name="Участие в мероприятии",
            field_type=FieldType.NUMERIC,
            points_per_unit=5.0,
            manual_count=2,
            cloud_link=""
        ),
    ]

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

    # Render ReportPreviewDialog with individual fields
    report_dlg = ReportPreviewDialog(win.config, tab=pm_tab)
    report_dlg.resize(760, 600)
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
