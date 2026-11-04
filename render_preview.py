"""Script to generate visual previews of EMS Reporter with latest features."""

import os
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.report_dialog import ReportPreviewDialog
from app.dialogs import EditLinksDialog
from app.theme import MEDICAL_QSS
from app.models import ReportField, FieldType, DepartmentTab, DiscordLinkItem


def create_demo_screenshot():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(MEDICAL_QSS)

    demo_dir = Path("/home/burmalda/Кирилл/EMS reporter/temp_demo")
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    demo_dir.mkdir(parents=True)

    day_city = demo_dir / "ПМП день (Город)"
    day_city.mkdir()
    for i in range(8):
        (day_city / f"screen_day_{i:02d}.png").write_text("dummy")

    night_city = demo_dir / "ПМП ночь (Город)"
    night_city.mkdir()
    for i in range(6):
        (night_city / f"screen_night_{i:02d}.png").write_text("dummy")

    demo_cfg = demo_dir / "demo_config.json"
    win = MainWindow(config_path=str(demo_cfg))
    win.name_edit.setText("Jason Mitsui")
    win.static_edit.setText("206277")

    # Save empty placeholder screenshot first
    win.resize(1160, 720)
    win.show()
    app.processEvents()
    empty_path = "/home/burmalda/Кирилл/EMS reporter/empty_preview.png"
    win.grab().save(empty_path)
    print(f"Empty preview saved to {empty_path}")

    # Now create a demo tab
    discord_items = [
        DiscordLinkItem(url="https://discord.com/channels/1182357036315451412/1182745050233458828/1567539641345773609", count=3),
        DiscordLinkItem(url="https://discord.com/channels/1182357036315451412/1182745050233458828/1567539349388656681", count=2),
        DiscordLinkItem(url="https://discord.com/channels/1182357036315451412/1182745050233458828/1567505934501023757", count=5),
    ]

    pm_tab = DepartmentTab(
        id="tab-pm",
        title="Paramedic (PM)",
        description="Скорая медицинская помощь (выезды, ПМП, реанимации, вызовы)",
        fields=[
            ReportField(
                id="fld-1",
                name="ПМП день (Город)",
                field_type=FieldType.FOLDER,
                folder_path=str(day_city),
                batch_mode_enabled=True,
                batch_size=4,
                batch_points=30.0,
                points_per_unit=2.0,
                cloud_link="https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoP"
            ),
            ReportField(
                id="fld-2",
                name="ПМП ночь (Город)",
                field_type=FieldType.FOLDER,
                folder_path=str(night_city),
                points_per_unit=3.0,
                cloud_link=""
            ),
            ReportField(
                id="fld-3",
                name="Участие в мероприятии",
                field_type=FieldType.NUMERIC,
                points_per_unit=5.0,
                manual_count=2,
                cloud_link=""
            ),
            ReportField(
                id="fld-4",
                name="Отчёты в спец. связи (Discord)",
                field_type=FieldType.LINKS,
                points_per_unit=3.0,
                links=discord_items,
                cloud_link=""
            ),
        ]
    )

    win.config.tabs = [pm_tab]
    win.rebuild_tabs()
    win.force_refresh_all()
    app.processEvents()

    screenshot_path = "/home/burmalda/Кирилл/EMS reporter/preview.png"
    win.grab().save(screenshot_path)
    print(f"Preview saved to {screenshot_path}")

    # Links dialog preview
    links_dlg = EditLinksDialog(
        field_name="Отчёты в спец. связи (Discord)",
        items=discord_items,
        points_per_unit=3.0
    )
    links_dlg.resize(740, 500)
    links_dlg.show()
    app.processEvents()
    links_path = "/home/burmalda/Кирилл/EMS reporter/links_dialog_preview.png"
    links_dlg.grab().save(links_path)
    print(f"Links dialog preview saved to {links_path}")
    links_dlg.close()

    # Report preview
    report_dlg = ReportPreviewDialog(win.config, tab=pm_tab)
    report_dlg.resize(780, 620)
    report_dlg.show()
    app.processEvents()
    report_path = "/home/burmalda/Кирилл/EMS reporter/report_preview.png"
    report_dlg.grab().save(report_path)
    print(f"Report preview saved to {report_path}")
    report_dlg.close()

    shutil.rmtree(demo_dir, ignore_errors=True)
    win.close()


if __name__ == "__main__":
    create_demo_screenshot()
