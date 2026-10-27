"""Field dialogs for adding and editing fields and tabs."""

from __future__ import annotations

import os
import uuid
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from app.models import ReportField, FieldType, DepartmentTab


class EditFieldDialog(QDialog):
    """Dialog to create or edit a field within a department tab."""

    def __init__(self, parent=None, field: Optional[ReportField] = None):
        super().__init__(parent)
        self.field = field
        self.result_field: Optional[ReportField] = None

        self.setWindowTitle("Настройка поля" if field else "Добавить новое поле")
        self.setFixedWidth(520)
        self.setup_ui()

        if field:
            self.load_field_data(field)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title / Description
        header = QLabel("🩺 Параметры отчётного поля")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        # Field Type selector
        type_layout = QVBoxLayout()
        type_lbl = QLabel("Тип поля:")
        type_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.type_combo = QComboBox()
        self.type_combo.addItem("📁 Папка со скриншотами (автоподсчёт файлов)", FieldType.FOLDER)
        self.type_combo.addItem("🔢 Числовое поле (ручной ввод)", FieldType.NUMERIC)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Name input
        name_layout = QVBoxLayout()
        name_lbl = QLabel("Название поля (действие в отчёте):")
        name_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Реанимация в городе (день) или Выдача таблеток")
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # Folder container (only for FieldType.FOLDER)
        self.folder_container = QFrame()
        folder_layout = QVBoxLayout(self.folder_container)
        folder_layout.setContentsMargins(0, 0, 0, 0)
        folder_layout.setSpacing(6)

        folder_lbl = QLabel("Путь к папке со скриншотами:")
        folder_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        folder_row = QHBoxLayout()
        self.folder_edit = QLineEdit()
        self.folder_edit.setPlaceholderText("Выберите папку, где лежат скриншоты...")
        
        self.browse_btn = QPushButton("📂 Обзор...")
        self.browse_btn.setObjectName("secondaryButton")
        self.browse_btn.clicked.connect(self.choose_folder)

        folder_row.addWidget(self.folder_edit)
        folder_row.addWidget(self.browse_btn)
        folder_layout.addWidget(folder_lbl)
        folder_layout.addLayout(folder_row)

        self.folder_info_lbl = QLabel("Файлы считаются автоматически (.png, .jpg, .jpeg, .webp)")
        self.folder_info_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        folder_layout.addWidget(self.folder_info_lbl)
        layout.addWidget(self.folder_container)

        # Numeric container (for FieldType.NUMERIC initial count)
        self.numeric_container = QFrame()
        numeric_layout = QVBoxLayout(self.numeric_container)
        numeric_layout.setContentsMargins(0, 0, 0, 0)
        numeric_layout.setSpacing(6)
        num_lbl = QLabel("Текущее значение (количество раз):")
        num_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.manual_spin = QSpinBox()
        self.manual_spin.setRange(0, 999999)
        self.manual_spin.setValue(0)
        numeric_layout.addWidget(num_lbl)
        numeric_layout.addWidget(self.manual_spin)
        layout.addWidget(self.numeric_container)
        self.numeric_container.hide()

        # Points per unit
        pts_layout = QVBoxLayout()
        pts_lbl = QLabel("Баллов за 1 скриншот / единицу:")
        pts_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.points_spin = QDoubleSpinBox()
        self.points_spin.setRange(0.0, 1000.0)
        self.points_spin.setSingleStep(0.5)
        self.points_spin.setDecimals(1)
        self.points_spin.setValue(2.0)
        pts_layout.addWidget(pts_lbl)
        pts_layout.addWidget(self.points_spin)
        layout.addLayout(pts_layout)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def on_type_changed(self, index: int):
        ft = self.type_combo.currentData()
        if ft == FieldType.FOLDER:
            self.folder_container.show()
            self.numeric_container.hide()
        else:
            self.folder_container.hide()
            self.numeric_container.show()

    def choose_folder(self):
        curr = self.folder_edit.text() if os.path.exists(self.folder_edit.text()) else ""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку со скриншотами", curr)
        if folder:
            self.folder_edit.setText(folder)

    def load_field_data(self, f: ReportField):
        idx = 0 if f.field_type == FieldType.FOLDER else 1
        self.type_combo.setCurrentIndex(idx)
        self.name_edit.setText(f.name)
        self.folder_edit.setText(f.folder_path)
        self.points_spin.setValue(f.points_per_unit)
        self.manual_spin.setValue(f.manual_count)
        self.on_type_changed(idx)

    def validate_and_save(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, укажите название поля.")
            self.name_edit.setFocus()
            return

        ft = self.type_combo.currentData()
        pts = self.points_spin.value()
        folder = self.folder_edit.text().strip() if ft == FieldType.FOLDER else ""
        manual = self.manual_spin.value() if ft == FieldType.NUMERIC else 0

        fid = self.field.id if self.field else str(uuid.uuid4())

        self.result_field = ReportField(
            id=fid,
            name=name,
            field_type=ft,
            folder_path=folder,
            points_per_unit=pts,
            manual_count=manual
        )
        self.accept()


class EditTabDialog(QDialog):
    """Dialog to create or edit a department tab."""

    def __init__(self, parent=None, tab: Optional[DepartmentTab] = None):
        super().__init__(parent)
        self.tab = tab
        self.result_tab: Optional[DepartmentTab] = None

        self.setWindowTitle("Настройка вкладки отдела" if tab else "Создать новую вкладку отдела")
        self.setFixedWidth(460)
        self.setup_ui()

        if tab:
            self.load_tab_data(tab)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("🏥 Отдел EMS / Вкладка")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        # Title
        title_lbl = QLabel("Название вкладки (отдела):")
        title_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например: Paramedic (PM) или Отдел интернатуры")
        layout.addWidget(title_lbl)
        layout.addWidget(self.title_edit)

        # Code
        code_lbl = QLabel("Короткий код / аббревиатура:")
        code_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("Например: PM, DI, PSED, HAD")
        layout.addWidget(code_lbl)
        layout.addWidget(self.code_edit)

        # Description
        desc_lbl = QLabel("Описание / обязанности отдела (необязательно):")
        desc_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Например: Скорая медицинская помощь, выезды по вызовам")
        layout.addWidget(desc_lbl)
        layout.addWidget(self.desc_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def load_tab_data(self, t: DepartmentTab):
        self.title_edit.setText(t.title)
        self.code_edit.setText(t.code)
        self.desc_edit.setText(t.description)

    def validate_and_save(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите название вкладки.")
            self.title_edit.setFocus()
            return

        code = self.code_edit.text().strip()
        desc = self.desc_edit.text().strip()

        tid = self.tab.id if self.tab else str(uuid.uuid4())
        fields = self.tab.fields if self.tab else []

        self.result_tab = DepartmentTab(
            id=tid,
            title=title,
            code=code,
            description=desc,
            fields=fields
        )
        self.accept()
