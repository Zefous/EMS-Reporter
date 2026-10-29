"""Interactive card widgets for ReportField (Folder, Numeric, and Links)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QFileDialog,
    QMessageBox,
    QMenu,
)

from app.models import ReportField, FieldType
from app.dialogs import EditFieldDialog, EditLinksDialog


class FieldCardWidget(QFrame):
    """Visual card for an individual report field with live updates."""

    changed = Signal()         # Emitted when value, path, or config changes
    deleted = Signal(str)      # Emitted with field_id when user deletes card
    moved_up = Signal(str)     # Emitted to reorder field up
    moved_down = Signal(str)   # Emitted to reorder field down

    def __init__(self, field: ReportField, parent=None):
        super().__init__(parent)
        self.field = field

        # Set styling class based on type
        if field.field_type == FieldType.NUMERIC:
            self.setProperty("class", "FieldCardNumeric")
        elif field.field_type == FieldType.LINKS:
            self.setProperty("class", "FieldCardLinks")
        else:
            self.setProperty("class", "FieldCard")

        self.setup_ui()
        self.refresh_display()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(14, 10, 14, 10)
        main_layout.setSpacing(14)

        # Left: Icon & Name & Path/Details
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)

        # Title row
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        if self.field.field_type == FieldType.FOLDER:
            icon_text = "📁"
        elif self.field.field_type == FieldType.NUMERIC:
            icon_text = "🔢"
        else:
            icon_text = "🔗"

        self.icon_lbl = QLabel(icon_text)
        self.icon_lbl.setStyleSheet("font-size: 16px;")

        self.title_lbl = QLabel(self.field.name)
        self.title_lbl.setStyleSheet("font-weight: 700; font-size: 14px; color: #f8fafc;")

        title_row.addWidget(self.icon_lbl)
        title_row.addWidget(self.title_lbl)
        title_row.addStretch()
        left_layout.addLayout(title_row)

        # Subtitle info
        if self.field.field_type == FieldType.FOLDER:
            folder_row = QHBoxLayout()
            folder_row.setSpacing(6)

            self.path_lbl = QLabel()
            self.path_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            self.update_path_label()

            self.pick_folder_btn = QPushButton("Выбрать папку")
            self.pick_folder_btn.setObjectName("secondaryButton")
            self.pick_folder_btn.setFixedHeight(26)
            self.pick_folder_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            self.pick_folder_btn.clicked.connect(self.select_folder)

            self.open_folder_btn = QPushButton("Открыть")
            self.open_folder_btn.setObjectName("secondaryButton")
            self.open_folder_btn.setFixedHeight(26)
            self.open_folder_btn.setStyleSheet("font-size: 11px; padding: 2px 8px;")
            self.open_folder_btn.clicked.connect(self.open_folder_in_os)

            folder_row.addWidget(self.path_lbl, 1)
            folder_row.addWidget(self.pick_folder_btn)
            folder_row.addWidget(self.open_folder_btn)
            left_layout.addLayout(folder_row)
        elif self.field.field_type == FieldType.LINKS:
            links_row = QHBoxLayout()
            links_row.setSpacing(8)

            self.info_lbl = QLabel()
            self.info_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

            self.links_btn = QPushButton("🔗 Ссылки (0)")
            self.links_btn.setObjectName("secondaryButton")
            self.links_btn.setFixedHeight(26)
            self.links_btn.setStyleSheet("font-size: 11px; padding: 2px 10px; color: #a5b4fc;")
            self.links_btn.clicked.connect(self.open_links_dialog)

            links_row.addWidget(self.info_lbl, 1)
            links_row.addWidget(self.links_btn)
            left_layout.addLayout(links_row)
        else:
            # Numeric field: note about points per unit
            self.info_lbl = QLabel()
            self.info_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
            left_layout.addWidget(self.info_lbl)

        main_layout.addLayout(left_layout, 2)

        # Middle: Numeric Controls (if numeric field)
        if self.field.field_type == FieldType.NUMERIC:
            mid_layout = QHBoxLayout()
            mid_layout.setSpacing(6)

            self.spin_count = QSpinBox()
            self.spin_count.setRange(0, 999999)
            self.spin_count.setValue(self.field.manual_count)
            self.spin_count.setFixedWidth(80)
            self.spin_count.setFixedHeight(30)
            self.spin_count.valueChanged.connect(self.on_spin_changed)

            mid_layout.addWidget(self.spin_count)
            main_layout.addLayout(mid_layout)

        # Right: Score Badge & Actions
        right_layout = QHBoxLayout()
        right_layout.setSpacing(10)

        # Badge: "(13 шт - 26 б)" - Selectable & copyable, but read-only
        self.badge_lbl = QLineEdit()
        self.badge_lbl.setReadOnly(True)
        self.badge_lbl.setAlignment(Qt.AlignCenter)
        if self.field.field_type == FieldType.NUMERIC:
            self.badge_lbl.setObjectName("badgeNumericScore")
        elif self.field.field_type == FieldType.LINKS:
            self.badge_lbl.setObjectName("badgeLinksScore")
        else:
            self.badge_lbl.setObjectName("badgeScore")
        self.badge_lbl.setFixedHeight(30)
        self.badge_lbl.setMinimumWidth(130)
        self.badge_lbl.setToolTip("Выделите текст мышью и скопируйте (Ctrl+C)")
        right_layout.addWidget(self.badge_lbl)

        # Actions buttons (Edit, Reorder, Delete)
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(4)

        self.up_btn = QPushButton("▲")
        self.up_btn.setObjectName("iconButton")
        self.up_btn.setFixedSize(26, 26)
        self.up_btn.setToolTip("Переместить выше")
        self.up_btn.clicked.connect(lambda: self.moved_up.emit(self.field.id))

        self.down_btn = QPushButton("▼")
        self.down_btn.setObjectName("iconButton")
        self.down_btn.setFixedSize(26, 26)
        self.down_btn.setToolTip("Переместить ниже")
        self.down_btn.clicked.connect(lambda: self.moved_down.emit(self.field.id))

        self.edit_btn = QPushButton("⚙")
        self.edit_btn.setObjectName("iconButton")
        self.edit_btn.setFixedSize(26, 26)
        self.edit_btn.setToolTip("Настроить поле")
        self.edit_btn.clicked.connect(self.edit_field)

        self.del_btn = QPushButton("✕")
        self.del_btn.setObjectName("iconButton")
        self.del_btn.setStyleSheet("color: #ef4444; font-weight: bold;")
        self.del_btn.setFixedSize(26, 26)
        self.del_btn.setToolTip("Удалить поле")
        self.del_btn.clicked.connect(self.confirm_delete)

        actions_layout.addWidget(self.up_btn)
        actions_layout.addWidget(self.down_btn)
        actions_layout.addWidget(self.edit_btn)
        actions_layout.addWidget(self.del_btn)
        right_layout.addLayout(actions_layout)

        main_layout.addLayout(right_layout)

    def update_path_label(self):
        if not hasattr(self, "path_lbl"):
            return
        pts_val = f"{int(self.field.points_per_unit)}" if self.field.points_per_unit.is_integer() else f"{self.field.points_per_unit:.1f}"
        if not self.field.folder_path:
            self.path_lbl.setText(f"⚠️ Папка не выбрана • ({pts_val} б/скриншот)")
            self.path_lbl.setStyleSheet("color: #eab308; font-size: 11px;")
        elif not os.path.exists(self.field.folder_path):
            self.path_lbl.setText(f"❌ Папка не найдена: {self.field.folder_path} • ({pts_val} б/скриншот)")
            self.path_lbl.setStyleSheet("color: #f87171; font-size: 11px;")
        else:
            # Shorten display if too long
            p = self.field.folder_path
            if len(p) > 45:
                p = "..." + p[-42:]
            self.path_lbl.setText(f"📁 {p} • ({pts_val} б/скриншот)")
            self.path_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")

    def update_info_label(self):
        if hasattr(self, "info_lbl"):
            pts_val = f"{int(self.field.points_per_unit)}" if self.field.points_per_unit.is_integer() else f"{self.field.points_per_unit:.1f}"
            if self.field.field_type == FieldType.LINKS:
                count = len(self.field.get_clean_links())
                self.info_lbl.setText(f"Ссылки на сообщения • Введено: {count} шт. • Ценность: {pts_val} б/ссылка")
                if hasattr(self, "links_btn"):
                    self.links_btn.setText(f"🔗 Ссылки ({count})")
            else:
                self.info_lbl.setText(f"Ручной ввод данных • Ценность: {pts_val} б. за единицу")

    def open_links_dialog(self):
        dlg = EditLinksDialog(
            self,
            field_name=self.field.name,
            links=self.field.links,
            points_per_unit=self.field.points_per_unit
        )
        if dlg.exec():
            self.field.links = dlg.result_links
            self.refresh_display()
            self.changed.emit()

    def select_folder(self):
        curr = self.field.folder_path if os.path.exists(self.field.folder_path) else ""
        folder = QFileDialog.getExistingDirectory(self, f"Выберите папку для: {self.field.name}", curr)
        if folder:
            self.field.folder_path = folder
            self.update_path_label()
            self.refresh_display()
            self.changed.emit()

    def open_folder_in_os(self):
        if not self.field.folder_path or not os.path.exists(self.field.folder_path):
            QMessageBox.information(self, "Папка", "Папка со скриншотами ещё не выбрана или не существует.")
            return

        p = self.field.folder_path
        try:
            if sys.platform == "win32":
                os.startfile(p)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", p])
            else:
                subprocess.Popen(["xdg-open", p])
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось открыть папку: {e}")

    def on_spin_changed(self, val: int):
        self.field.manual_count = val
        self.refresh_display()
        self.changed.emit()

    def edit_field(self):
        dlg = EditFieldDialog(self, field=self.field)
        if dlg.exec():
            rf = dlg.result_field
            if rf:
                self.field.name = rf.name
                self.field.field_type = rf.field_type
                self.field.folder_path = rf.folder_path
                self.field.points_per_unit = rf.points_per_unit
                self.field.manual_count = rf.manual_count
                self.field.links = rf.links
                self.field.cloud_link = rf.cloud_link
                self.title_lbl.setText(self.field.name)
                self.refresh_display()
                self.changed.emit()

    def confirm_delete(self):
        reply = QMessageBox.question(
            self,
            "Удаление поля",
            f"Вы уверены, что хотите удалить поле:\n«{self.field.name}»?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.deleted.emit(self.field.id)

    def refresh_display(self):
        """Update badge text e.g. '(13 шт - 26 б)' and labels."""
        badge_text = self.field.format_status_text()
        self.badge_lbl.setText(badge_text)
        self.update_path_label()
        self.update_info_label()
