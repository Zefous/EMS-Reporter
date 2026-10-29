"""Tab content widget containing fields for one EMS department."""

from __future__ import annotations

from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QMessageBox,
)

from app.models import DepartmentTab, ReportField, FieldType
from app.field_widget import FieldCardWidget
from app.dialogs import EditFieldDialog, EditTabDialog


class TabPageWidget(QWidget):
    """View containing all fields and controls for a single department tab."""

    tab_changed = Signal()         # Emitted when anything inside tab changes
    delete_tab_requested = Signal(str)  # Emitted to delete this tab
    edit_tab_requested = Signal(str)    # Emitted to edit tab title/info

    def __init__(self, tab: DepartmentTab, parent=None):
        super().__init__(parent)
        self.tab = tab
        self.field_cards: List[FieldCardWidget] = []

        self.setup_ui()
        self.rebuild_fields()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Tab top toolbar: Description, Subtotal, and Action Buttons
        top_bar = QFrame()
        top_bar.setStyleSheet("background-color: #0f2234; border: 1px solid #1a3650; border-radius: 8px; padding: 8px 14px;")
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # Left: department description & subtotal
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        self.tab_desc_lbl = QLabel(self.tab.description or "Настраиваемый отдел EMS")
        self.tab_desc_lbl.setStyleSheet("color: #94a3b8; font-size: 12px; font-style: italic;")

        self.subtotal_lbl = QLabel()
        self.subtotal_lbl.setStyleSheet("color: #38bdf8; font-size: 13px; font-weight: 700;")
        self.update_subtotal_label()

        info_layout.addWidget(self.tab_desc_lbl)
        info_layout.addWidget(self.subtotal_lbl)
        top_layout.addLayout(info_layout, 1)

        # Right: Buttons for tab management
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.add_field_btn = QPushButton("➕ Добавить поле")
        self.add_field_btn.setObjectName("primaryButton")
        self.add_field_btn.clicked.connect(self.add_field)

        self.refresh_btn = QPushButton("🔄 Пересчитать")
        self.refresh_btn.setObjectName("secondaryButton")
        self.refresh_btn.setToolTip("Пересчитать файлы во всех папках этого отдела")
        self.refresh_btn.clicked.connect(self.refresh_all_fields)

        self.edit_tab_btn = QPushButton("⚙ Отдел")
        self.edit_tab_btn.setObjectName("secondaryButton")
        self.edit_tab_btn.setToolTip("Редактировать название или описание этой вкладки")
        self.edit_tab_btn.clicked.connect(lambda: self.edit_tab_requested.emit(self.tab.id))

        self.del_tab_btn = QPushButton("🗑 Удалить отдел")
        self.del_tab_btn.setObjectName("dangerButton")
        self.del_tab_btn.setToolTip("Удалить этот отдел и все его поля")
        self.del_tab_btn.clicked.connect(lambda: self.delete_tab_requested.emit(self.tab.id))

        btn_layout.addWidget(self.add_field_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.edit_tab_btn)
        btn_layout.addWidget(self.del_tab_btn)
        top_layout.addLayout(btn_layout)

        main_layout.addWidget(top_bar)

        # Scroll Area for field cards
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.scroll_content = QWidget()
        self.fields_layout = QVBoxLayout(self.scroll_content)
        self.fields_layout.setContentsMargins(0, 4, 4, 4)
        self.fields_layout.setSpacing(10)
        self.fields_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll, 1)

    def update_subtotal_label(self):
        tot_pts = self.tab.total_points()
        tot_count = self.tab.total_count()
        pts_str = f"{int(tot_pts)}" if tot_pts.is_integer() else f"{tot_pts:.1f}"
        self.subtotal_lbl.setText(f"Итого по отделу: {tot_count} выполнено • {pts_str} баллов")

    def rebuild_fields(self):
        """Clear and recreate all field cards."""
        # Clear existing
        for card in self.field_cards:
            self.fields_layout.removeWidget(card)
            card.deleteLater()
        self.field_cards.clear()

        # Add cards
        for f in self.tab.fields:
            card = FieldCardWidget(f, self.scroll_content)
            card.changed.connect(self.on_field_changed)
            card.type_changed.connect(self.rebuild_fields)
            card.deleted.connect(self.on_field_deleted)
            card.moved_up.connect(self.on_field_moved_up)
            card.moved_down.connect(self.on_field_moved_down)

            # Insert before the stretch at the end
            self.fields_layout.insertWidget(self.fields_layout.count() - 1, card)
            self.field_cards.append(card)

        self.update_subtotal_label()

    def add_field(self):
        dlg = EditFieldDialog(self)
        if dlg.exec():
            rf = dlg.result_field
            if rf:
                self.tab.fields.append(rf)
                self.rebuild_fields()
                self.tab_changed.emit()

    def on_field_changed(self):
        self.update_subtotal_label()
        self.tab_changed.emit()

    def on_field_deleted(self, field_id: str):
        self.tab.fields = [f for f in self.tab.fields if f.id != field_id]
        self.rebuild_fields()
        self.tab_changed.emit()

    def on_field_moved_up(self, field_id: str):
        idx = next((i for i, f in enumerate(self.tab.fields) if f.id == field_id), -1)
        if idx > 0:
            self.tab.fields[idx], self.tab.fields[idx - 1] = self.tab.fields[idx - 1], self.tab.fields[idx]
            self.rebuild_fields()
            self.tab_changed.emit()

    def on_field_moved_down(self, field_id: str):
        idx = next((i for i, f in enumerate(self.tab.fields) if f.id == field_id), -1)
        if idx >= 0 and idx < len(self.tab.fields) - 1:
            self.tab.fields[idx], self.tab.fields[idx + 1] = self.tab.fields[idx + 1], self.tab.fields[idx]
            self.rebuild_fields()
            self.tab_changed.emit()

    def refresh_all_fields(self):
        """Re-scan folder counts and update UI."""
        for card in self.field_cards:
            card.refresh_display()
        self.update_subtotal_label()
        self.tab_changed.emit()
