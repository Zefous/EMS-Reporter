"""UI and widget tests running in headless/offscreen Qt mode."""

import os
import tempfile
import pytest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType, DiscordLinkItem
from app.main_window import MainWindow
from app.theme import MEDICAL_QSS
from app.report_dialog import ReportPreviewDialog, ReportFieldItem
from app.field_widget import FieldCardWidget
from app.dialogs import EditLinksDialog, EditFieldDialog, EditTabDialog


@pytest.fixture(scope="session")
def qapp():
    """Ensure QApplication instance is initialized for offscreen tests."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
        app.setStyleSheet(MEDICAL_QSS)
    return app


def test_main_window_lifecycle_and_empty_placeholder(qapp):
    """Verify MainWindow initializes cleanly with empty placeholder when no tabs exist."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.show()

        # Requirement 1: No pre-created tabs, empty placeholder shown
        assert window.tab_widget.count() == 0
        assert window.empty_placeholder.isVisible() is True
        assert "0 шт • 0 б" in window.stats_badge.text()

        # Requirement 2: Rank edit removed
        assert not hasattr(window, "rank_edit")

        # Change player info
        window.name_edit.setText("Jason Mitsui")
        window.static_edit.setText("206277")
        assert window.config.player_name == "Jason Mitsui"
        assert window.config.player_static == "206277"

        # Add a tab
        new_tab = DepartmentTab(id="tab-1", title="Paramedic (PM)", fields=[])
        window.config.tabs.append(new_tab)
        window.rebuild_tabs()

        assert window.tab_widget.count() == 1
        assert window.empty_placeholder.isVisible() is False

        # Add a numeric field
        test_field = ReportField(
            id="f-num-test",
            name="Участие в мероприятии",
            field_type=FieldType.NUMERIC,
            points_per_unit=5.0,
            manual_count=2
        )
        new_tab.fields.append(test_field)
        pm_tab_widget = window.tab_widgets[new_tab.id]
        pm_tab_widget.rebuild_fields()
        window.update_totals()

        assert len(pm_tab_widget.field_cards) == 1
        card = pm_tab_widget.field_cards[0]

        # Badge must be selectable & copyable
        assert card.badge_lbl.isReadOnly() is True
        assert card.badge_lbl.text() == "(2 шт - 10 б)"

        # Changing manual count
        card.spin_count.setValue(3)
        assert card.badge_lbl.text() == "(3 шт - 15 б)"

        # Top-right stats badge
        assert "3 шт • 15 б" in window.stats_badge.text()

        window.close()


def test_report_dialog_individual_fields(qapp):
    """Verify ReportPreviewDialog renders individual fields without quotes and with task counts."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_gui_config.json"
        window = MainWindow(config_path=str(config_path))
        window.config.player_name = "Jason Mitsui"
        window.config.player_static = "206277"

        pm_tab = DepartmentTab(id="t1", title="Paramedic (PM)", fields=[
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
            ),
            ReportField(
                id="f3",
                name="Отчёты в спец. связи",
                field_type=FieldType.LINKS,
                points_per_unit=3.0,
                links=[
                    DiscordLinkItem(url="https://discord.com/msg1", count=3),
                    DiscordLinkItem(url="https://discord.com/msg2", count=2),
                ]
            )
        ])

        dlg = ReportPreviewDialog(window.config, tab=pm_tab)
        dlg.show()

        # Check field items count: 1 (Player) + 3 (Fields) + 1 (Total) = 5
        assert len(dlg.field_items) == 5

        # Field 1: Player info
        assert dlg.field_items[0].title == "Имя Фамилия | статик"
        assert dlg.field_items[0].get_text() == 'Jason Mitsui | 206277'

        # Field 2: Cloud link + status
        assert dlg.field_items[1].title == "ПМП день (Город)"
        assert dlg.field_items[1].get_text() == 'https://drive.google.com/folder1 (10 шт - 20 б)'

        # Field 3: Without cloud link
        assert dlg.field_items[2].title == "ПМП ночь (Город)"
        assert dlg.field_items[2].get_text() == '(6 шт - 18 б)'

        # Field 4: Discord links with individual counts and subtotal
        assert dlg.field_items[3].title == "Отчёты в спец. связи"
        f3_text = dlg.field_items[3].get_text()
        assert "https://discord.com/msg1 (3 шт - 9 б)" in f3_text
        assert "https://discord.com/msg2 (2 шт - 6 б)" in f3_text
        assert "(5 шт - 15 б)" in f3_text

        # Field 5: Total points (20 + 18 + 15 = 53)
        assert dlg.field_items[4].title == "Общее количество баллов"
        assert dlg.field_items[4].get_text() == '53'

        dlg.close()
        window.close()


def test_links_card_and_edit_dialog(qapp):
    """Verify links field card and EditLinksDialog with task quantities per link."""
    items = [
        DiscordLinkItem(url="https://discord.com/1", count=2),
        DiscordLinkItem(url="https://discord.com/2", count=3)
    ]
    field = ReportField(
        id="lnk-gui",
        name="Отчёты в спец. связи (Discord)",
        field_type=FieldType.LINKS,
        points_per_unit=4.0,
        links=items
    )
    card = FieldCardWidget(field)

    # 2 + 3 = 5 tasks * 4 = 20 pts
    assert card.badge_lbl.text() == "(5 шт - 20 б)"
    assert "Всего задач: 5 шт." in card.info_lbl.text()
    assert card.links_btn.text() == "🔗 Ссылки (2)"

    # Test EditLinksDialog
    dlg = EditLinksDialog(parent=card, field_name=field.name, items=field.get_discord_link_items(), points_per_unit=field.points_per_unit)
    assert "Ссылок: 2 шт." in dlg.stats_lbl.text()
    assert "20 б." in dlg.stats_lbl.text()

    # Add a row
    new_row = dlg.add_row(DiscordLinkItem(url="https://discord.com/3", count=4))
    assert "Ссылок: 3 шт." in dlg.stats_lbl.text()
    # 5 + 4 = 9 tasks * 4 = 36 pts
    assert "36 б." in dlg.stats_lbl.text()

    dlg.validate_and_save()
    assert len(dlg.result_items) == 3

    card.deleteLater()
    dlg.deleteLater()
    qapp.processEvents()


def test_active_tab_only_stats_badge(qapp):
    """Verify top-right stats badge counts only fields from the active tab."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_active_tab_stats.json"
        window = MainWindow(config_path=str(config_path))
        window.show()

        tab0 = DepartmentTab(id="t0", title="Вкладка 1", fields=[
            ReportField(id="f0", name="Действие 1", field_type=FieldType.NUMERIC, points_per_unit=5.0, manual_count=2)
        ])
        tab1 = DepartmentTab(id="t1", title="Вкладка 2", fields=[
            ReportField(id="f1", name="Действие 2", field_type=FieldType.NUMERIC, points_per_unit=10.0, manual_count=5)
        ])

        window.config.tabs = [tab0, tab1]
        window.rebuild_tabs()

        # When Tab 0 is selected
        window.tab_widget.setCurrentIndex(0)
        assert "2 шт • 10 б" in window.stats_badge.text()

        # Switch to Tab 1
        window.tab_widget.setCurrentIndex(1)
        assert "5 шт • 50 б" in window.stats_badge.text()

        window.close()


def test_edit_tab_dialog_clean_structure_and_enter_key(qapp):
    """Verify EditTabDialog has no code/abbreviation field, and Enter key saves."""
    from PySide6.QtGui import QKeyEvent

    dlg = EditTabDialog()
    dlg.show()

    # Verify no code_edit exists
    assert not hasattr(dlg, "code_edit")

    # Enter title
    dlg.title_edit.setText("Тестовая вкладка")
    dlg.desc_edit.setText("Описание вкладки")

    # Simulate pressing Enter
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result_tab is not None
    assert dlg.result_tab.title == "Тестовая вкладка"
    assert dlg.result_tab.description == "Описание вкладки"

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_edit_field_dialog_enter_key(qapp):
    """Verify EditFieldDialog executes save on Enter key."""
    from PySide6.QtGui import QKeyEvent

    dlg = EditFieldDialog()
    dlg.show()

    dlg.name_edit.setText("Тестовое поле Enter")
    dlg.points_spin.setValue(3.5)

    # Press Enter
    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result_field is not None
    assert dlg.result_field.name == "Тестовое поле Enter"
    assert dlg.result_field.points_per_unit == 3.5

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()
