"""Field and tab dialogs for EMS Reporter."""

from __future__ import annotations

import os
import uuid
from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from app.models import ReportField, FieldType, DepartmentTab


class EditLinksDialog(QDialog):
    """Dedicated modal dialog to paste, view, and count Discord / message links."""

    def __init__(
        self,
        parent=None,
        field_name: str = "",
        links: Optional[List[str]] = None,
        points_per_unit: float = 1.0
    ):
        super().__init__(parent)
        self.field_name = field_name
        self.points_per_unit = points_per_unit
        self.result_links: List[str] = []

        self.setWindowTitle(f"🔗 Ссылки на сообщения: {field_name}")
        self.resize(680, 520)
        self.setMinimumSize(550, 400)

        self.setup_ui()
        if links:
            self.editor.setPlainText("\n".join(links))
        self.update_stats()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header Frame
        header = QFrame()
        header.setStyleSheet("background-color: #0f2234; border: 1px solid #1a3650; border-radius: 8px; padding: 10px 14px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        title = QLabel(f"🔗 Ссылки на сообщения в Discord: {self.field_name}")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #818cf8;")
        desc = QLabel(
            "Вставьте ссылки на сообщения из Discord (по одной ссылке на строку).\n"
            "Программа автоматически подсчитает количество ссылок и начислит баллы."
        )
        desc.setStyleSheet("font-size: 11px; color: #94a3b8;")

        h_layout.addWidget(title)
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Stats bar + Quick Actions
        action_bar = QHBoxLayout()
        action_bar.setSpacing(10)

        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("font-size: 13px; font-weight: 700; color: #38bdf8;")
        action_bar.addWidget(self.stats_lbl, 1)

        self.paste_btn = QPushButton("📋 Вставить из буфера")
        self.paste_btn.setObjectName("secondaryButton")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)

        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_editor)

        action_bar.addWidget(self.paste_btn)
        action_bar.addWidget(self.clear_btn)
        layout.addLayout(action_bar)

        # Editor
        self.editor = QPlainTextEdit()
        self.editor.setPlaceholderText(
            "Пример:\n"
            "https://discord.com/channels/...\n"
            "https://discord.com/channels/...\n"
            "https://discord.com/channels/..."
        )
        self.editor.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; background-color: #07101b;"
        )
        self.editor.textChanged.connect(self.update_stats)
        layout.addWidget(self.editor, 1)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("💾 Сохранить ссылки")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def get_lines(self) -> List[str]:
        return [line.strip() for line in self.editor.toPlainText().splitlines() if line.strip()]

    def update_stats(self):
        lines = self.get_lines()
        count = len(lines)
        pts = round(count * self.points_per_unit, 2)
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        rate_str = f"{int(self.points_per_unit)}" if self.points_per_unit.is_integer() else f"{self.points_per_unit:.1f}"
        self.stats_lbl.setText(f"Ссылок: {count} шт. • Итого: {pts_str} б. ({rate_str} б/ед)")

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        if text:
            cur = self.editor.toPlainText().strip()
            if cur:
                self.editor.setPlainText(cur + "\n" + text.strip())
            else:
                self.editor.setPlainText(text.strip())

    def clear_editor(self):
        self.editor.clear()

    def validate_and_save(self):
        self.result_links = self.get_lines()
        self.accept()


class EditFieldDialog(QDialog):
    """Dialog to create or edit a field within a department tab."""

    def __init__(self, parent=None, field: Optional[ReportField] = None):
        super().__init__(parent)
        self.field = field
        self.result_field: Optional[ReportField] = None

        self.setWindowTitle("Настройка поля" if field else "Добавить новое поле")
        self.setFixedWidth(540)
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
        self.type_combo.addItem("🔗 Ссылки на сообщения (Discord и др.)", FieldType.LINKS)
        self.type_combo.currentIndexChanged.connect(self.on_type_changed)
        type_layout.addWidget(type_lbl)
        type_layout.addWidget(self.type_combo)
        layout.addLayout(type_layout)

        # Name input
        name_layout = QVBoxLayout()
        name_lbl = QLabel("Название поля (действие в отчёте):")
        name_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Например: Реанимация в городе (день) или Отчёт в Discord")
        name_layout.addWidget(name_lbl)
        name_layout.addWidget(self.name_edit)
        layout.addLayout(name_layout)

        # 1. Folder container (only for FieldType.FOLDER)
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

        # 2. Numeric container (for FieldType.NUMERIC)
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

        # 3. Links container (for FieldType.LINKS)
        self.links_container = QFrame()
        links_box = QVBoxLayout(self.links_container)
        links_box.setContentsMargins(0, 0, 0, 0)
        links_box.setSpacing(6)
        links_lbl = QLabel("Ссылки на сообщения в Discord (по одной на строку):")
        links_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.links_edit = QPlainTextEdit()
        self.links_edit.setPlaceholderText("https://discord.com/channels/...\nhttps://discord.com/channels/...")
        self.links_edit.setFixedHeight(95)
        self.links_edit.setStyleSheet("font-family: 'Consolas', monospace; font-size: 11px; background-color: #07101b;")
        links_hint = QLabel("Каждая непустая строка считается как 1 ссылка. Можно также дополнять с карточки поля.")
        links_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        links_box.addWidget(links_lbl)
        links_box.addWidget(self.links_edit)
        links_box.addWidget(links_hint)
        layout.addWidget(self.links_container)
        self.links_container.hide()

        # Points per unit
        pts_layout = QVBoxLayout()
        self.pts_lbl = QLabel("Баллов за 1 скриншот / единицу / ссылку:")
        self.pts_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.points_spin = QDoubleSpinBox()
        self.points_spin.setRange(0.0, 1000.0)
        self.points_spin.setSingleStep(0.5)
        self.points_spin.setDecimals(1)
        self.points_spin.setValue(2.0)
        pts_layout.addWidget(self.pts_lbl)
        pts_layout.addWidget(self.points_spin)
        layout.addLayout(pts_layout)

        # Cloud Link (Optional, for all field types)
        link_layout = QVBoxLayout()
        link_lbl = QLabel("Ссылка на облачное хранилище (Google Диск, Imgur и др., необязательно):")
        link_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.cloud_link_edit = QLineEdit()
        self.cloud_link_edit.setPlaceholderText("https://drive.google.com/drive/folders/... или https://imgur.com/...")
        link_hint = QLabel("Используется при формировании отчёта (не отображается на главном экране)")
        link_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        link_layout.addWidget(link_lbl)
        link_layout.addWidget(self.cloud_link_edit)
        link_layout.addWidget(link_hint)
        layout.addLayout(link_layout)

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
            self.links_container.hide()
            self.pts_lbl.setText("Баллов за 1 скриншот:")
        elif ft == FieldType.NUMERIC:
            self.folder_container.hide()
            self.numeric_container.show()
            self.links_container.hide()
            self.pts_lbl.setText("Баллов за 1 единицу действия:")
        elif ft == FieldType.LINKS:
            self.folder_container.hide()
            self.numeric_container.hide()
            self.links_container.show()
            self.pts_lbl.setText("Баллов за 1 ссылку на сообщение:")

    def choose_folder(self):
        curr = self.folder_edit.text() if os.path.exists(self.folder_edit.text()) else ""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку со скриншотами", curr)
        if folder:
            self.folder_edit.setText(folder)

    def load_field_data(self, f: ReportField):
        if f.field_type == FieldType.FOLDER:
            idx = 0
        elif f.field_type == FieldType.NUMERIC:
            idx = 1
        else:
            idx = 2

        self.type_combo.setCurrentIndex(idx)
        self.name_edit.setText(f.name)
        self.folder_edit.setText(f.folder_path)
        self.points_spin.setValue(f.points_per_unit)
        self.manual_spin.setValue(f.manual_count)
        self.links_edit.setPlainText("\n".join(f.links))
        self.cloud_link_edit.setText(f.cloud_link or "")
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
        links = [l.strip() for l in self.links_edit.toPlainText().splitlines() if l.strip()] if ft == FieldType.LINKS else []
        cloud_link = self.cloud_link_edit.text().strip()

        fid = self.field.id if self.field else str(uuid.uuid4())

        self.result_field = ReportField(
            id=fid,
            name=name,
            field_type=ft,
            folder_path=folder,
            points_per_unit=pts,
            manual_count=manual,
            links=links,
            cloud_link=cloud_link
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
