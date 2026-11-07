"""Script to generate visual previews of EMS Reporter with all 4 field types."""

import os
import shutil
import tempfile
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow
from app.report_dialog import ReportPreviewDialog
from app.dialogs import EditLinksDialog, EditSimpleLinksDialog
from app.about_dialog import AboutDialog
from app.help_dialog import HelpDialog
from app.export_import_dialogs import ExportDialog
from app.updater import ReleaseInfo
from app.update_dialog import UpdateDialog
from app.theme import MEDICAL_QSS
from app.models import ReportField, FieldType, DepartmentTab, DiscordLinkItem


def create_demo_screenshot():
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance() or QApplication([])
    app.setStyleSheet(MEDICAL_QSS)

    docs_dir = Path("/home/burmalda/Кирилл/EMS reporter/docs")
    docs_dir.mkdir(parents=True, exist_ok=True)

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
    empty_path = docs_dir / "empty_preview.png"
    win.grab().save(str(empty_path))
    print(f"Empty preview saved to {empty_path}")

    # Now create a demo tab with all 4 field types
    discord_task_items = [
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
                name="Аудиты в спец. связи (баллы за ссылку)",
                field_type=FieldType.LINKS,
                points_per_unit=5.0,
                simple_links=[
                    "https://discord.com/channels/104928192837/104928192838/1298371928374",
                    "https://discord.com/channels/104928192837/104928192838/1298371928375"
                ],
                cloud_link=""
            ),
            ReportField(
                id="fld-5",
                name="Отчёты в спец. связи (с подсчётом задач)",
                field_type=FieldType.LINKS_WITH_TASKS,
                points_per_unit=3.0,
                links=discord_task_items,
                cloud_link=""
            ),
            ReportField(
                id="fld-6",
                name="Реанимация за городом (ночь)",
                field_type=FieldType.FOLDER,
                folder_path="",
                points_per_unit=4.0,
                cloud_link=""
            ),
        ]
    )

    win.config.tabs = [pm_tab]
    win.rebuild_tabs()
    win.force_refresh_all()
    app.processEvents()

    screenshot_path = docs_dir / "preview.png"
    win.grab().save(str(screenshot_path))
    print(f"Preview saved to {screenshot_path}")

    # Export Dialog preview
    export_dlg = ExportDialog(win.config, active_tab=pm_tab)
    export_dlg.show()
    app.processEvents()
    export_path = docs_dir / "export_preview.png"
    export_dlg.grab().save(str(export_path))
    print(f"Export preview saved to {export_path}")
    export_dlg.close()

    # About Dialog preview
    about_dlg = AboutDialog()
    about_dlg.show()
    app.processEvents()
    about_path = docs_dir / "about_preview.png"
    about_dlg.grab().save(str(about_path))
    print(f"About preview saved to {about_path}")
    about_dlg.close()

    # Update Dialog preview
    mock_rel = ReleaseInfo(
        tag_name="v1.2.0",
        version="1.2.0",
        name="EMS Reporter v1.2.0",
        body="• Добавлена система бесшовного обновления в один клик\n• Повышена стабильность работы на Windows\n• Обновлён интерфейс и автотесты",
        html_url="https://github.com/Zefous/EMS-Reporter/releases",
        download_url="https://github.com/Zefous/EMS-Reporter/releases/download/v1.2.0/EMS_Reporter.exe",
        asset_name="EMS_Reporter.exe",
        asset_size=64500000,
    )
    upd_dlg = UpdateDialog(mock_rel)
    upd_dlg.show()
    app.processEvents()
    upd_path = docs_dir / "update_preview.png"
    upd_dlg.grab().save(str(upd_path))
    print(f"Update preview saved to {upd_path}")
    upd_dlg.close()

    # Help Dialog preview
    help_dlg = HelpDialog()
    help_dlg.resize(960, 640)
    help_dlg.show()
    app.processEvents()
    help_path = docs_dir / "help_preview.png"
    help_dlg.grab().save(str(help_path))
    print(f"Help preview saved to {help_path}")
    help_dlg.close()

    # Links dialog preview
    links_dlg = EditLinksDialog(
        field_name="Отчёты в спец. связи (с подсчётом задач)",
        items=discord_task_items,
        points_per_unit=3.0
    )
    links_dlg.resize(740, 500)
    links_dlg.show()
    app.processEvents()
    links_path = docs_dir / "links_dialog_preview.png"
    links_dlg.grab().save(str(links_path))
    print(f"Links dialog preview saved to {links_path}")
    links_dlg.close()

    # Report preview
    report_dlg = ReportPreviewDialog(win.config, tab=pm_tab)
    report_dlg.resize(780, 680)
    report_dlg.show()
    app.processEvents()
    report_path = docs_dir / "report_preview.png"
    report_dlg.grab().save(str(report_path))
    print(f"Report preview saved to {report_path}")
    report_dlg.close()

    shutil.rmtree(demo_dir, ignore_errors=True)
    win.close()

    shutil.rmtree(demo_dir, ignore_errors=True)
    win.close()


if __name__ == "__main__":
    create_demo_screenshot()
