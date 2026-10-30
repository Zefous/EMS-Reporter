"""Main Application Window for EMS Reporter."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, Dict

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QMessageBox,
    QFileDialog,
    QStatusBar,
    QSplitter,
)

from app.models import ReporterConfig, DepartmentTab, ReportField, FieldType
from app.storage import ConfigManager, ReportGenerator
from app.templates import create_default_config
from app.dialogs import EditTabDialog
from app.tab_page import TabPageWidget
from app.report_dialog import ReportPreviewDialog


class MainWindow(QMainWindow):
    """Main window with dynamic medical department tabs and live score counting."""

    def __init__(self, config_path: Optional[str] = None):
        super().__init__()
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load()
        self.tab_widgets: Dict[str, TabPageWidget] = {}

        self.setWindowTitle("EMS Reporter - Majestic GTA V RP")
        self._centered_on_screen = False
        self.setup_ui()
        self.rebuild_tabs()
        self.update_totals()
        self.center_and_fit_screen()

        # Background auto-refresh timer for folder screenshot counts
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.auto_refresh_folders)
        if self.config.auto_refresh_seconds > 0:
            self.refresh_timer.start(self.config.auto_refresh_seconds * 1000)

    def showEvent(self, event):
        super().showEvent(event)
        if not self._centered_on_screen:
            self._centered_on_screen = True
            self.center_and_fit_screen()

    def center_and_fit_screen(self):
        """Fit window cleanly within the screen work area and center it."""
        if QApplication.platformName() == "offscreen":
            self.resize(1200, 780)
            return

        screen = self.screen() or QApplication.primaryScreen()
        if not screen:
            self.resize(1160, 750)
            return

        avail = screen.availableGeometry()

        # Usable screen bounds with safe margins
        max_w = max(600, avail.width() - 40)
        max_h = max(400, avail.height() - 40)

        target_w = min(1160, max_w)
        target_h = min(750, max_h)

        self.setMinimumSize(min(760, max_w), min(480, max_h))
        self.resize(target_w, target_h)

        # Center firmly inside the visible screen bounds (never negative coordinates)
        x = avail.x() + max(0, (avail.width() - target_w) // 2)
        y = avail.y() + max(0, (avail.height() - target_h) // 2)
        self.setGeometry(max(avail.x(), x), max(avail.y(), y), target_w, target_h)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header Banner (Medical Style)
        header = QFrame()
        header.setObjectName("headerBanner")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 12, 18, 12)
        header_layout.setSpacing(16)

        # Hospital / EMS Identity
        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        title_lbl = QLabel("🚑 EMERGENCY MEDICAL SERVICES • MAJESTIC RP")
        title_lbl.setObjectName("headerTitle")

        subtitle_lbl = QLabel("Автоматический учёт баллов отчётов по скриншотам и ручным нормативам")
        subtitle_lbl.setObjectName("headerSubtitle")

        title_box.addWidget(title_lbl)
        title_box.addWidget(subtitle_lbl)
        header_layout.addLayout(title_box, 3)

        # Player profile inputs (Name & Static ID)
        player_box = QHBoxLayout()
        player_box.setSpacing(6)

        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Имя Фамилия")
        self.name_edit.setText(self.config.player_name)
        self.name_edit.setFixedWidth(120)
        self.name_edit.textChanged.connect(self.on_player_info_changed)

        self.static_edit = QLineEdit()
        self.static_edit.setPlaceholderText("Статик #ID")
        self.static_edit.setText(self.config.player_static)
        self.static_edit.setFixedWidth(75)
        self.static_edit.textChanged.connect(self.on_player_info_changed)

        self.rank_edit = QLineEdit()
        self.rank_edit.setPlaceholderText("Ранг / Должность")
        self.rank_edit.setText(self.config.rank)
        self.rank_edit.setFixedWidth(120)
        self.rank_edit.textChanged.connect(self.on_player_info_changed)

        player_box.addWidget(QLabel("Сотрудник:"))
        player_box.addWidget(self.name_edit)
        player_box.addWidget(self.static_edit)
        player_box.addWidget(self.rank_edit)
        header_layout.addLayout(player_box)

        # Summary Stats Badge (Total actions & Total points)
        stats_card = QFrame()
        stats_card.setObjectName("statsCard")
        stats_layout = QVBoxLayout(stats_card)
        stats_layout.setContentsMargins(12, 4, 12, 4)
        stats_layout.setSpacing(1)

        self.stats_title = QLabel("ОБЩИЙ ИТОГ")
        self.stats_title.setStyleSheet("font-size: 10px; font-weight: 700; color: #38bdf8; letter-spacing: 0.5px;")
        self.stats_title.setAlignment(Qt.AlignCenter)

        self.stats_badge = QLabel("0 шт • 0 б")
        self.stats_badge.setObjectName("statsTotalBadge")
        self.stats_badge.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(self.stats_title)
        stats_layout.addWidget(self.stats_badge)
        header_layout.addWidget(stats_card)

        main_layout.addWidget(header)

        # 2. Main Action Toolbar (Add Tab, Import, Export, Report, Refresh)
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #0b1725; border-bottom: 1px solid #162a3f; padding: 6px 16px;")
        tool_layout = QHBoxLayout(toolbar)
        tool_layout.setContentsMargins(0, 0, 0, 0)
        tool_layout.setSpacing(8)

        self.add_tab_btn = QPushButton("➕ Добавить вкладку")
        self.add_tab_btn.setObjectName("primaryButton")
        self.add_tab_btn.clicked.connect(self.create_tab)

        self.generate_report_btn = QPushButton("📝 Сформировать отчёт")
        self.generate_report_btn.setObjectName("successButton")
        self.generate_report_btn.clicked.connect(self.open_report_dialog)

        self.rescan_btn = QPushButton("🔄 Пересчитать папки")
        self.rescan_btn.setObjectName("secondaryButton")
        self.rescan_btn.clicked.connect(self.force_refresh_all)

        tool_layout.addWidget(self.add_tab_btn)
        tool_layout.addWidget(self.generate_report_btn)
        tool_layout.addWidget(self.rescan_btn)
        tool_layout.addStretch()

        # Config Import / Export / Reset
        self.export_btn = QPushButton("📤 Экспорт")
        self.export_btn.setObjectName("secondaryButton")
        self.export_btn.setToolTip("Сохранить файл настроек вкладок и полей, чтобы отправить другим игрокам")
        self.export_btn.clicked.connect(self.export_config)

        self.import_btn = QPushButton("📥 Импорт")
        self.import_btn.setObjectName("secondaryButton")
        self.import_btn.setToolTip("Загрузить файл настроек вкладок и полей, полученный от другого игрока")
        self.import_btn.clicked.connect(self.import_config)

        self.reset_btn = QPushButton("↺ Сброс")
        self.reset_btn.setObjectName("secondaryButton")
        self.reset_btn.setToolTip("Восстановить стандартные вкладки (PM, DI, PSED, HAD)")
        self.reset_btn.clicked.connect(self.reset_to_default)

        tool_layout.addWidget(self.export_btn)
        tool_layout.addWidget(self.import_btn)
        tool_layout.addWidget(self.reset_btn)

        main_layout.addWidget(toolbar)

        # 3. Department Tabs Container
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 12)
        body_layout.setSpacing(8)

        self.tab_widget = QTabWidget()
        self.tab_widget.setMovable(True)
        self.tab_widget.currentChanged.connect(self.on_tab_switched)
        self.tab_widget.tabBar().tabMoved.connect(self.on_tab_moved)

        body_layout.addWidget(self.tab_widget)
        main_layout.addWidget(body, 1)

        # 4. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("EMS Reporter готов к работе")

    def rebuild_tabs(self):
        """Reconstruct tab widget from config."""
        self.tab_widget.blockSignals(True)
        self.tab_widget.clear()
        self.tab_widgets.clear()

        selected_index = 0
        for idx, tab in enumerate(self.config.tabs):
            tab_page = TabPageWidget(tab, self.tab_widget)
            tab_page.tab_changed.connect(self.on_data_changed)
            tab_page.delete_tab_requested.connect(self.delete_tab)
            tab_page.edit_tab_requested.connect(self.edit_tab)

            title = tab.title.replace("&", "&&")

            self.tab_widget.addTab(tab_page, title)
            self.tab_widgets[tab.id] = tab_page

            if self.config.active_tab_id == tab.id:
                selected_index = idx

        if self.tab_widget.count() > 0:
            self.tab_widget.setCurrentIndex(selected_index)

        self.tab_widget.blockSignals(False)
        self.update_totals()

    def create_tab(self):
        dlg = EditTabDialog(self)
        if dlg.exec():
            rt = dlg.result_tab
            if rt:
                self.config.tabs.append(rt)
                self.config.active_tab_id = rt.id
                self.rebuild_tabs()
                self.save_current_config()
                self.status_bar.showMessage(f"Создана новая вкладка: {rt.title}", 4000)

    def edit_tab(self, tab_id: str):
        tab = next((t for t in self.config.tabs if t.id == tab_id), None)
        if not tab:
            return

        dlg = EditTabDialog(self, tab=tab)
        if dlg.exec():
            rt = dlg.result_tab
            if rt:
                tab.title = rt.title
                tab.code = rt.code
                tab.description = rt.description
                self.rebuild_tabs()
                self.save_current_config()
                self.status_bar.showMessage(f"Обновлены параметры вкладки: {tab.title}", 4000)

    def delete_tab(self, tab_id: str):
        tab = next((t for t in self.config.tabs if t.id == tab_id), None)
        if not tab:
            return

        reply = QMessageBox.question(
            self,
            "Удаление вкладки",
            f"Вы уверены, что хотите удалить вкладку «{tab.title}» со всеми настроенными полями?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config.tabs = [t for t in self.config.tabs if t.id != tab_id]
            self.rebuild_tabs()
            self.save_current_config()
            self.status_bar.showMessage(f"Вкладка удалена", 3000)

    def on_tab_switched(self, index: int):
        if 0 <= index < len(self.config.tabs):
            self.config.active_tab_id = self.config.tabs[index].id
            self.save_current_config()
        self.update_totals()

    def on_tab_moved(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.config.tabs) and 0 <= to_idx < len(self.config.tabs):
            moved = self.config.tabs.pop(from_idx)
            self.config.tabs.insert(to_idx, moved)
            self.save_current_config()
        self.update_totals()

    def on_player_info_changed(self):
        self.config.player_name = self.name_edit.text()
        self.config.player_static = self.static_edit.text()
        self.config.rank = self.rank_edit.text()
        self.save_current_config()

    def on_data_changed(self):
        self.update_totals()
        self.save_current_config()

    def update_totals(self):
        current_idx = self.tab_widget.currentIndex()
        if 0 <= current_idx < len(self.config.tabs):
            active_tab = self.config.tabs[current_idx]
            count = active_tab.total_count()
            pts = active_tab.total_points()
        else:
            count = 0
            pts = 0.0
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        self.stats_badge.setText(f"{count} шт • {pts_str} б")

    def auto_refresh_folders(self):
        """Silently refresh folder counters."""
        current_page = self.tab_widget.currentWidget()
        if isinstance(current_page, TabPageWidget):
            current_page.refresh_all_fields()
        self.update_totals()

    def force_refresh_all(self):
        """Manual full refresh of all tabs."""
        for page in self.tab_widgets.values():
            page.refresh_all_fields()
        self.update_totals()
        self.status_bar.showMessage("Все папки со скриншотами пересчитаны", 3000)

    def save_current_config(self):
        self.config_manager.save(self.config)

    def open_report_dialog(self):
        # Refresh all tabs before showing
        self.force_refresh_all()
        current_idx = self.tab_widget.currentIndex()
        active_tab = self.config.tabs[current_idx] if 0 <= current_idx < len(self.config.tabs) else None
        dlg = ReportPreviewDialog(self.config, tab=active_tab, parent=self)
        dlg.exec()

    def export_config(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Экспортировать настройки EMS Reporter",
            "ems_preset_settings.json",
            "JSON files (*.json);;All files (*.*)"
        )
        if path:
            try:
                ConfigManager.export_to_file(self.config, path)
                QMessageBox.information(
                    self,
                    "Экспорт завершён",
                    f"Настройки успешно сохранены в файл:\n{path}\n\nВы можете отправить этот файл коллегам по фракции."
                )
            except Exception as e:
                QMessageBox.warning(self, "Ошибка экспорта", f"Не удалось сохранить настройки: {e}")

    def import_config(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Импортировать настройки EMS Reporter",
            "",
            "JSON files (*.json);;All files (*.*)"
        )
        if path:
            try:
                imported = ConfigManager.import_from_file(path)
                reply = QMessageBox.question(
                    self,
                    "Подтверждение импорта",
                    f"Загрузить настройки из файла?\nБудет загружено {len(imported.tabs)} вкладок.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.config = imported
                    self.name_edit.setText(self.config.player_name)
                    self.static_edit.setText(self.config.player_static)
                    self.rank_edit.setText(self.config.rank)
                    self.rebuild_tabs()
                    self.save_current_config()
                    QMessageBox.information(self, "Импорт завершён", "Настройки успешно применены!")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка импорта", f"Не удалось прочитать файл настроек:\n{e}")

    def reset_to_default(self):
        reply = QMessageBox.question(
            self,
            "Сброс настроек",
            "Сбросить структуру вкладок к стандартным (PM, DI, PSED, HAD)?\n"
            "Текущие настроенные пути и поля будут заменены стандартными шаблонами.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.config = create_default_config()
            self.name_edit.setText(self.config.player_name)
            self.static_edit.setText(self.config.player_static)
            self.rank_edit.setText(self.config.rank)
            self.rebuild_tabs()
            self.save_current_config()
            self.status_bar.showMessage("Восстановлены стандартные настройки вкладок", 4000)
