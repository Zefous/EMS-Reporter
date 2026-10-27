"""UI and widget tests running in headless/offscreen Qt mode."""

import os
import tempfile
import pytest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType
from app.main_window import MainWindow
from app.theme import MEDICAL_QSS
from app.report_dialog import ReportPreviewDialog, ReportFieldItem
from app.field_widget import FieldCardWidget


@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication instance is initialized for offscreen tests."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setStyleSheet(MEDICAL_QSS)
    return app


def test_main_window_lifecycle_and_ui(qapp):
    """Verify MainWindow initializes cleanly, loads tabs with 0 fields by default."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.show()

        # Check tabs count (4 default tabs: PM, DI, PSED, HAD)
        assert window.tab_widget.count() == 4
        assert "Paramedic" in window.tab_widget.tabText(0)

        # By requirement #2: All tabs should have NO pre-created fields
        pm_tab_widget = window.tab_widgets[window.config.tabs[0].id]
        assert len(pm_tab_widget.field_cards) == 0

        # Change player info
        window.name_edit.setText("Jason Mitsui")
        window.static_edit.setText("206277")
        window.rank_edit.setText("Paramedic")
        assert window.config.player_name == "Jason Mitsui"
        assert window.config.player_static == "206277"

        # Now add a numeric field programmatically to test live badge and editing
        test_field = ReportField(
            id="f-num-test",
            name="Участие в мероприятии",
            field_type=FieldType.NUMERIC,
            points_per_unit=5.0,
            manual_count=2
        )
        window.config.tabs[0].fields.append(test_field)
        pm_tab_widget.rebuild_fields()
        window.update_totals()

        assert len(pm_tab_widget.field_cards) == 1
        card = pm_tab_widget.field_cards[0]

        # Requirement #3: Badge must be selectable and copyable, but read-only
        assert card.badge_lbl.isReadOnly() is True
        assert card.badge_lbl.text() == "(2 шт - 10 б)"

        # Requirement #1: Changing points_per_unit must update the info label under title
        assert "Ценность: 5 б. за единицу" in card.info_lbl.text()
        card.field.points_per_unit = 7.0
        card.refresh_display()
        assert "Ценность: 7 б. за единицу" in card.info_lbl.text()
        assert card.badge_lbl.text() == "(2 шт - 14 б)"

        # Changing manual count
        card.spin_count.setValue(3)
        assert card.badge_lbl.text() == "(3 шт - 21 б)"

        # Grab screenshot
        pixmap = window.grab()
        assert not pixmap.isNull()

        window.close()


def test_report_dialog_individual_fields(qapp):
    """Verify ReportPreviewDialog renders individual fields according to requirement #5."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.config.player_name = "Jason Mitsui"
        window.config.player_static = "206277"

        pm_tab = window.config.tabs[0]
        pm_tab.fields = [
            ReportField(
                id="f1",
                name="ПМП день (Город)",
                field_type=FieldType.NUMERIC,
                points_per_unit=2.0,
                manual_count=10,
                cloud_link="https://drive.google.com/folder1"
            ),
            ReportField(
                id="f2",
                name="ПМП ночь (Город)",
                field_type=FieldType.NUMERIC,
                points_per_unit=3.0,
                manual_count=6,
                cloud_link=""
            )
        ]

        dlg = ReportPreviewDialog(window.config, tab=pm_tab)
        dlg.show()

        # Check field items count: 1 (Player) + 2 (Fields) + 1 (Total) = 4
        assert len(dlg.field_items) == 4

        # Field 1: Player info
        assert dlg.field_items[0].title == "Имя Фамилия | статик"
        assert dlg.field_items[0].get_text() == 'Jason Mitsui | 206277'

        # Field 2: Cloud link + status
        assert dlg.field_items[1].title == "ПМП день (Город)"
        assert dlg.field_items[1].get_text() == 'https://drive.google.com/folder1 (10 шт - 20 б)'

        # Field 3: Without cloud link
        assert dlg.field_items[2].title == "ПМП ночь (Город)"
        assert dlg.field_items[2].get_text() == '(6 шт - 18 б)'

        # Field 4: Total points
        assert dlg.field_items[3].title == "Общее количество баллов"
        assert dlg.field_items[3].get_text() == '38'

        # Test copying individual item
        dlg.field_items[1].copy_value()
        assert QApplication.clipboard().text() == 'https://drive.google.com/folder1 (10 шт - 20 б)'

        # Test copying entire report text
        dlg.copy_all_report()
        clipboard_text = QApplication.clipboard().text()
        assert "Имя Фамилия | статик" in clipboard_text
        assert "Jason Mitsui | 206277" in clipboard_text
        assert "ПМП день (Город)" in clipboard_text
        assert "Общее количество баллов" in clipboard_text
        assert "38" in clipboard_text

        dlg.close()
        window.close()
