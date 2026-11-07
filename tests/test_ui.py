"""UI and widget tests running in headless/offscreen Qt mode."""

import os
import tempfile
import pytest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType, DiscordLinkItem
from app.main_window import MainWindow
from app.theme import MEDICAL_QSS
from app.report_dialog import ReportPreviewDialog, ReportFieldItem
from app.field_widget import FieldCardWidget
from app.dialogs import EditLinksDialog, EditSimpleLinksDialog, EditFieldDialog, EditTabDialog
from app.about_dialog import AboutDialog
from app.help_dialog import HelpDialog
from app.export_import_dialogs import ExportDialog, ImportOptionsDialog
from app.updater import ReleaseInfo
from app.update_dialog import UpdateDialog


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
                name="Простые ссылки",
                field_type=FieldType.LINKS,
                points_per_unit=2.0,
                simple_links=["https://discord.com/p1", "https://discord.com/p2"]
            ),
            ReportField(
                id="f4",
                name="Отчёты в спец. связи с задачами",
                field_type=FieldType.LINKS_WITH_TASKS,
                points_per_unit=3.0,
                links=[
                    DiscordLinkItem(url="https://discord.com/msg1", count=3),
                    DiscordLinkItem(url="https://discord.com/msg2", count=2),
                ]
            ),
            ReportField(
                id="f5",
                name="Нулевое действие",
                field_type=FieldType.NUMERIC,
                points_per_unit=2.0,
                manual_count=0
            )
        ])

        dlg = ReportPreviewDialog(window.config, tab=pm_tab)
        dlg.show()

        # Check field items count: 1 (Player) + 5 (Fields) + 1 (Total) = 7
        assert len(dlg.field_items) == 7

        # Field 1: Player info
        assert dlg.field_items[0].title == "Имя Фамилия | статик"
        assert dlg.field_items[0].get_text() == 'Jason Mitsui | 206277'

        # Field 2: Cloud link + status
        assert dlg.field_items[1].title == "ПМП день (Город)"
        assert dlg.field_items[1].get_text() == 'https://drive.google.com/folder1 (10 шт - 20 б)'

        # Field 3: Without cloud link
        assert dlg.field_items[2].title == "ПМП ночь (Город)"
        assert dlg.field_items[2].get_text() == '(6 шт - 18 б)'

        # Field 4: Simple links
        assert dlg.field_items[3].title == "Простые ссылки"
        f3_text = dlg.field_items[3].get_text()
        assert "https://discord.com/p1" in f3_text
        assert "(2 шт - 4 б)" in f3_text

        # Field 5: Discord links with individual counts and subtotal
        assert dlg.field_items[4].title == "Отчёты в спец. связи с задачами"
        f4_text = dlg.field_items[4].get_text()
        assert "https://discord.com/msg1 (3 шт - 9 б)" in f4_text
        assert "https://discord.com/msg2 (2 шт - 6 б)" in f4_text
        assert "(5 шт - 15 б)" in f4_text

        # Field 6: Zero points field -> Requirement 1: must be just "-"
        assert dlg.field_items[5].title == "Нулевое действие"
        assert dlg.field_items[5].get_text() == '-'

        # Field 7: Total points (20 + 18 + 4 + 15 = 57)
        assert dlg.field_items[6].title == "Общее количество баллов"
        assert dlg.field_items[6].get_text() == '57'

        dlg.close()
        window.close()


def test_simple_links_card_and_dialog(qapp):
    """Verify simple links field card and EditSimpleLinksDialog."""
    field = ReportField(
        id="simple-lnk-gui",
        name="Аудиты в Discord",
        field_type=FieldType.LINKS,
        points_per_unit=5.0,
        simple_links=["https://discord.com/1", "https://discord.com/2"]
    )
    card = FieldCardWidget(field)
    assert card.badge_lbl.text() == "(2 шт - 10 б)"
    assert "Введено: 2 шт." in card.info_lbl.text()
    assert card.icon_lbl.text() == "🔗"

    dlg = EditSimpleLinksDialog(parent=card, field_name=field.name, links=field.simple_links, points_per_unit=field.points_per_unit)
    assert "Ссылок: 2 шт." in dlg.stats_lbl.text()
    assert "10 б." in dlg.stats_lbl.text()

    dlg.editor.appendPlainText("https://discord.com/3")
    assert "Ссылок: 3 шт." in dlg.stats_lbl.text()
    assert "15 б." in dlg.stats_lbl.text()

    dlg.validate_and_save()
    assert len(dlg.result_links) == 3

    card.deleteLater()
    dlg.deleteLater()
    qapp.processEvents()


def test_links_with_tasks_card_and_dialog(qapp):
    """Verify links with tasks field card and EditLinksDialog."""
    items = [
        DiscordLinkItem(url="https://discord.com/1", count=2),
        DiscordLinkItem(url="https://discord.com/2", count=3)
    ]
    field = ReportField(
        id="tasks-lnk-gui",
        name="Отчёты в спец. связи с задачами",
        field_type=FieldType.LINKS_WITH_TASKS,
        points_per_unit=4.0,
        links=items
    )
    card = FieldCardWidget(field)

    assert card.badge_lbl.text() == "(5 шт - 20 б)"
    assert "Всего задач: 5 шт." in card.info_lbl.text()
    assert card.icon_lbl.text() == "💬"

    dlg = EditLinksDialog(parent=card, field_name=field.name, items=field.get_discord_link_items(), points_per_unit=field.points_per_unit)
    assert "Ссылок: 2 шт." in dlg.stats_lbl.text()
    assert "20 б." in dlg.stats_lbl.text()

    new_row = dlg.add_row(DiscordLinkItem(url="https://discord.com/3", count=4))
    assert "Ссылок: 3 шт." in dlg.stats_lbl.text()
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

    assert not hasattr(dlg, "code_edit")

    dlg.title_edit.setText("Тестовая вкладка")
    dlg.desc_edit.setText("Описание вкладки")

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result_tab is not None
    assert dlg.result_tab.title == "Тестовая вкладка"
    assert dlg.result_tab.description == "Описание вкладки"

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_edit_field_dialog_all_four_types_and_enter_key(qapp):
    """Verify EditFieldDialog supports all four types and saves on Enter."""
    from PySide6.QtGui import QKeyEvent

    dlg = EditFieldDialog()
    dlg.show()

    assert dlg.type_combo.count() == 4
    assert dlg.type_combo.itemData(0) == FieldType.FOLDER
    assert dlg.type_combo.itemData(1) == FieldType.NUMERIC
    assert dlg.type_combo.itemData(2) == FieldType.LINKS
    assert dlg.type_combo.itemData(3) == FieldType.LINKS_WITH_TASKS

    # Switch to FieldType.LINKS
    dlg.type_combo.setCurrentIndex(2)
    assert dlg.simple_links_container.isVisible() is True
    assert dlg.tasks_links_container.isVisible() is False
    assert dlg.cloud_link_container.isVisible() is False

    # Switch to FieldType.LINKS_WITH_TASKS
    dlg.type_combo.setCurrentIndex(3)
    assert dlg.simple_links_container.isVisible() is False
    assert dlg.tasks_links_container.isVisible() is True
    assert dlg.cloud_link_container.isVisible() is False

    dlg.name_edit.setText("Тестовое поле Enter")
    dlg.points_spin.setValue(3.5)

    event = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)
    dlg.keyPressEvent(event)

    assert dlg.result_field is not None
    assert dlg.result_field.name == "Тестовое поле Enter"
    assert dlg.result_field.points_per_unit == 3.5
    assert dlg.result_field.field_type == FieldType.LINKS_WITH_TASKS

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_about_dialog(qapp):
    """Verify AboutDialog contains description, version, github link and releases link."""
    dlg = AboutDialog()
    dlg.show()

    assert "EMS Reporter" in dlg.windowTitle()
    labels = dlg.findChildren(QLabel)
    texts = " ".join([l.text() for l in labels])
    assert "https://github.com/Zefous/EMS-Reporter" in texts
    assert "https://github.com/Zefous/EMS-Reporter/releases" in texts
    assert "Majestic GTA V RP" in texts
    assert "Версия 1.1.0" in texts

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_help_dialog_tree_and_articles(qapp):
    """Verify HelpDialog contains left navigation tree without build_exe item."""
    dlg = HelpDialog()
    dlg.show()

    assert "Руководство пользователя" in dlg.windowTitle()
    assert dlg.tree.topLevelItemCount() == 5  # intro, tabs, fields, report, config (no build_exe)

    # Verify build_exe is not in tree
    all_titles = []
    for i in range(dlg.tree.topLevelItemCount()):
        all_titles.append(dlg.tree.topLevelItem(i).text(0))
    assert not any("Сборка в автономный" in t for t in all_titles)

    # Check first item text
    intro_item = dlg.tree.topLevelItem(0)
    dlg.tree.setCurrentItem(intro_item)
    qapp.processEvents()
    assert "Руководство пользователя EMS Reporter" in dlg.browser.toHtml()

    # Check second item (Tabs)
    tabs_item = dlg.tree.topLevelItem(1)
    dlg.tree.setCurrentItem(tabs_item)
    qapp.processEvents()
    assert "Управление вкладками" in dlg.browser.toHtml()

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_export_options_dialog(qapp):
    """Verify ExportDialog options (clean template vs full data, active tab only vs all)."""
    config = ReporterConfig(player_name="Jason Mitsui", player_static="206277", tabs=[
        DepartmentTab(id="tab-1", title="Вкладка 1", fields=[
            ReportField(id="f1", name="Поле 1", field_type=FieldType.FOLDER, folder_path="/fake/path", manual_count=5, cloud_link="https://cloud")
        ]),
        DepartmentTab(id="tab-2", title="Вкладка 2", fields=[
            ReportField(id="f2", name="Поле 2", field_type=FieldType.NUMERIC, points_per_unit=5.0, manual_count=3)
        ])
    ])

    dlg = ExportDialog(config, active_tab=config.tabs[0])
    dlg.show()

    # Default is template
    assert dlg.radio_template.isChecked() is True
    assert dlg.chk_active_only.isChecked() is False

    # Test create_export_copy as template, active only
    tpl_copy = config.create_export_copy(as_template=True, active_tab_only=True, active_tab_id="tab-1")
    assert len(tpl_copy.tabs) == 1
    assert tpl_copy.tabs[0].title == "Вкладка 1"
    assert tpl_copy.player_name == ""
    assert tpl_copy.tabs[0].fields[0].folder_path == ""
    assert tpl_copy.tabs[0].fields[0].cloud_link == ""
    assert tpl_copy.tabs[0].fields[0].manual_count == 0

    # Test create_export_copy full data, all tabs
    full_copy = config.create_export_copy(as_template=False, active_tab_only=False)
    assert len(full_copy.tabs) == 2
    assert full_copy.player_name == "Jason Mitsui"
    assert full_copy.tabs[0].fields[0].folder_path == "/fake/path"
    assert full_copy.tabs[0].fields[0].cloud_link == "https://cloud"

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()


def test_import_options_dialog_and_append_mode(qapp):
    """Verify ImportOptionsDialog and append mode without deleting existing tabs."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        config_path = Path(tmp_dir) / "test_import_config.json"
        window = MainWindow(config_path=str(config_path))
        window.show()

        # Add initial tab
        initial_tab = DepartmentTab(id="t-init", title="Моя старая вкладка", fields=[])
        window.config.tabs = [initial_tab]
        window.rebuild_tabs()
        assert window.tab_widget.count() == 1

        # Prepare imported config with same ID to test ID regeneration
        imported = ReporterConfig(player_name="New Player", player_static="999", tabs=[
            DepartmentTab(id="t-init", title="Новая импортированная вкладка", fields=[])
        ])

        dlg = ImportOptionsDialog("test.json", imported, current_tabs_count=1)
        dlg.show()
        assert dlg.radio_append.isChecked() is True

        # Simulate append selection
        dlg.radio_append.setChecked(True)
        dlg.perform_import()
        assert dlg.selected_mode == "append"

        # Apply append in window
        for tab in imported.tabs:
            if tab.id in {t.id for t in window.config.tabs}:
                cloned = tab.clone_with_new_ids()
            else:
                cloned = tab
            window.config.tabs.append(cloned)

        window.rebuild_tabs()

        # Verify old tab was NOT deleted and new tab was appended
        assert window.tab_widget.count() == 2
        assert window.config.tabs[0].title == "Моя старая вкладка"
        assert window.config.tabs[1].title == "Новая импортированная вкладка"
        # IDs must be different
        assert window.config.tabs[0].id != window.config.tabs[1].id

        dlg.close()
        dlg.deleteLater()
        window.close()
        qapp.processEvents()


def test_update_dialog_ui(qapp):
    """Verify UpdateDialog renders release notes, version change and buttons."""
    release = ReleaseInfo(
        tag_name="v1.2.0",
        version="1.2.0",
        name="Версия 1.2.0",
        body="• Новая классная функция\n• Исправление ошибок",
        html_url="https://github.com/Zefous/EMS-Reporter/releases/tag/v1.2.0",
        download_url="https://github.com/Zefous/EMS-Reporter/releases/download/v1.2.0/EMS_Reporter.exe",
        asset_name="EMS_Reporter.exe",
        asset_size=62000000,
    )
    dlg = UpdateDialog(release)
    dlg.show()

    assert "Обновление" in dlg.windowTitle()
    assert "v1.2.0" in dlg.release.tag_name
    assert "Новая классная функция" in dlg.browser.toHtml()
    assert dlg.progress_container.isVisible() is False
    assert dlg.action_btn.text() == "⬇ Загрузить и обновить"

    dlg.close()
    dlg.deleteLater()
    qapp.processEvents()
