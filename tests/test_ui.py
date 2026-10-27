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
from app.report_dialog import ReportPreviewDialog


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
    """Verify MainWindow initializes cleanly, loads tabs, and updates totals."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.show()

        # Check tabs count (4 default tabs: PM, DI, PSED, HAD)
        assert window.tab_widget.count() == 4
        assert "Paramedic" in window.tab_widget.tabText(0)

        # Check total initial points (0)
        assert "0 шт • 0 б" in window.stats_badge.text()

        # Change player info
        window.name_edit.setText("Dmitry Sidorov")
        window.static_edit.setText("#54321")
        window.rank_edit.setText("Surgeon")
        assert window.config.player_name == "Dmitry Sidorov"
        assert window.config.player_static == "#54321"

        # Check Paramedic tab fields
        pm_tab_widget = window.tab_widgets[window.config.tabs[0].id]
        assert len(pm_tab_widget.field_cards) == 11

        # Simulate changing numeric count on a card
        # Find numeric field card
        num_cards = [c for c in pm_tab_widget.field_cards if c.field.field_type == FieldType.NUMERIC]
        assert len(num_cards) >= 3

        first_num_card = num_cards[0]  # "Участие в мероприятии", 5 pts
        first_num_card.spin_count.setValue(4)  # 4 * 5 = 20 pts
        assert first_num_card.field.manual_count == 4
        assert first_num_card.badge_lbl.text() == "(4 шт - 20 б)"

        # Check that window total updated
        assert "4 шт • 20 б" in window.stats_badge.text()

        # Render window to a screenshot pixmap to ensure styling renders without crash
        pixmap = window.grab()
        assert not pixmap.isNull()
        assert pixmap.width() > 0
        assert pixmap.height() > 0

        window.close()


def test_report_dialog_rendering(qapp):
    """Verify ReportPreviewDialog opens, updates text, and clipboard actions work."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.config.player_name = "Alex Stone"
        window.config.tabs[0].fields[0].manual_count = 5

        dlg = ReportPreviewDialog(window.config, current_tab_id=window.config.tabs[0].id)
        assert "Alex Stone" in dlg.text_edit.toPlainText()
        assert "ОТЧЁТ О ПРОДЕЛАННОЙ РАБОТЕ EMS" in dlg.text_edit.toPlainText()

        dlg.copy_to_clipboard()
        assert "скопирован" in dlg.status_msg_lbl.text().lower()
        dlg.close()
        window.close()
