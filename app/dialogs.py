"""Field and tab dialogs for EMS Reporter."""

from __future__ import annotations

import os
import re
import uuid
from typing import Optional, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QComboBox,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from app.models import ReportField, FieldType, DepartmentTab, DiscordLinkItem
from app.smooth_scroll import SmoothScrollArea


class LinkRowWidget(QWidget):
    """Single row representing one Discord link with its task count."""

    def __init__(
        self,
        item: DiscordLinkItem,
        points_per_unit: float,
        on_changed,
        on_delete,
        parent=None
    ):
        super().__init__(parent)
        self.item = item
        self.points_per_unit = points_per_unit
        self.on_changed = on_changed
        self.on_delete = on_delete

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # URL edit
        self.url_edit = QLineEdit(item.url)
        self.url_edit.setPlaceholderText("https://discord.com/channels/...")
        self.url_edit.textChanged.connect(self._url_changed)

        # Tasks count spin
        tasks_lbl = QLabel("Задач:")
        tasks_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.spin = QSpinBox()
        self.spin.setRange(1, 999999)
        self.spin.setValue(max(1, item.count))
        self.spin.setFixedWidth(70)
        self.spin.valueChanged.connect(self._count_changed)

        # Row points preview badge
        self.pts_lbl = QLabel()
        self.pts_lbl.setStyleSheet("color: #a5b4fc; font-weight: 700; font-size: 11px; min-width: 90px;")
        self._update_pts()

        # Delete button
        self.del_btn = QPushButton("✕")
        self.del_btn.setObjectName("iconButton")
        self.del_btn.setStyleSheet("color: #ef4444; font-weight: bold;")
        self.del_btn.setFixedSize(24, 24)
        self.del_btn.setToolTip("Удалить эту ссылку")
        self.del_btn.clicked.connect(lambda: self.on_delete(self))

        layout.addWidget(self.url_edit, 1)
        layout.addWidget(tasks_lbl)
        layout.addWidget(self.spin)
        layout.addWidget(self.pts_lbl)
        layout.addWidget(self.del_btn)

    def _url_changed(self, text: str):
        self.item.url = text.strip()
        self.on_changed()

    def _count_changed(self, val: int):
        self.item.count = val
        self._update_pts()
        self.on_changed()

    def set_rate(self, rate: float):
        self.points_per_unit = rate
        self._update_pts()

    def _update_pts(self):
        pts = round(self.item.count * self.points_per_unit, 2)
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        self.pts_lbl.setText(f"({self.item.count} шт - {pts_str} б)")


class EditLinksDialog(QDialog):
    """Dialog to manage Discord links with quantity of tasks per link."""

    def __init__(
        self,
        parent=None,
        field_name: str = "",
        items: Optional[List[DiscordLinkItem]] = None,
        points_per_unit: float = 1.0
    ):
        super().__init__(parent)
        self.field_name = field_name
        self.points_per_unit = points_per_unit
        self.result_items: List[DiscordLinkItem] = []
        self.row_widgets: List[LinkRowWidget] = []

        self.setWindowTitle(f"🔗 Ссылки на сообщения: {field_name}")
        self.resize(740, 520)
        self.setMinimumSize(580, 400)

        self.setup_ui()

        # Populate rows
        if items:
            for it in items:
                self.add_row(DiscordLinkItem(url=it.url, count=it.count))
        else:
            self.add_row(DiscordLinkItem(url="", count=1))

        self.update_stats()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        # Header Frame
        header = QFrame()
        header.setStyleSheet("background-color: #0f2234; border: 1px solid #1a3650; border-radius: 6px; padding: 8px 12px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        title = QLabel(f"🔗 Ссылки на сообщения: {self.field_name}")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #818cf8;")
        desc = QLabel(
            "Для каждой ссылки укажите количество выполненных задач. "
            "Баллы рассчитываются как: (Кол-во задач × Баллы за единицу)."
        )
        desc.setStyleSheet("font-size: 11px; color: #94a3b8;")

        h_layout.addWidget(title)
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Action bar & stats
        action_bar = QHBoxLayout()
        action_bar.setSpacing(8)

        self.stats_lbl = QLabel()
        self.stats_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #38bdf8;")
        action_bar.addWidget(self.stats_lbl, 1)

        self.add_btn = QPushButton("➕ Добавить ссылку")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(lambda: self.add_row())

        self.paste_btn = QPushButton("📋 Вставить из буфера")
        self.paste_btn.setObjectName("secondaryButton")
        self.paste_btn.clicked.connect(self.paste_from_clipboard)

        self.clear_btn = QPushButton("🗑 Очистить")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_all_rows)

        action_bar.addWidget(self.add_btn)
        action_bar.addWidget(self.paste_btn)
        action_bar.addWidget(self.clear_btn)
        layout.addLayout(action_bar)

        # Smooth Scroll Area for rows
        self.scroll = SmoothScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.rows_layout = QVBoxLayout(self.scroll_content)
        self.rows_layout.setContentsMargins(4, 4, 4, 4)
        self.rows_layout.setSpacing(6)
        self.rows_layout.addStretch()

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("💾 Сохранить ссылки")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def add_row(self, item: Optional[DiscordLinkItem] = None) -> LinkRowWidget:
        if item is None:
            item = DiscordLinkItem(url="", count=1)

        row = LinkRowWidget(
            item,
            self.points_per_unit,
            on_changed=self.update_stats,
            on_delete=self.remove_row,
            parent=self.scroll_content
        )
        self.rows_layout.insertWidget(self.rows_layout.count() - 1, row)
        self.row_widgets.append(row)
        self.update_stats()
        return row

    def remove_row(self, row: LinkRowWidget):
        if row in self.row_widgets:
            self.row_widgets.remove(row)
            self.rows_layout.removeWidget(row)
            row.deleteLater()
            self.update_stats()

    def clear_all_rows(self):
        for r in list(self.row_widgets):
            self.remove_row(r)
        self.add_row()

    def update_stats(self):
        valid = [r.item for r in self.row_widgets if r.item.url.strip()]
        link_count = len(valid)
        total_tasks = sum(it.count for it in valid)
        pts = round(total_tasks * self.points_per_unit, 2)
        pts_str = f"{int(pts)}" if pts.is_integer() else f"{pts:.1f}"
        rate_str = f"{int(self.points_per_unit)}" if self.points_per_unit.is_integer() else f"{self.points_per_unit:.1f}"
        self.stats_lbl.setText(f"Ссылок: {link_count} шт. • Всего задач: {total_tasks} шт. • Итого: {pts_str} б. ({rate_str} б/ед)")

    def paste_from_clipboard(self):
        text = QApplication.clipboard().text()
        if not text:
            return

        lines = [line.strip() for line in text.splitlines() if line.strip()]
        for line in lines:
            # Check if line contains a URL and possibly a count
            # e.g. "https://discord.com/... (3 шт - 9 б)" or "https://discord.com/... 3"
            count = 1
            url = line
            # Regex for number near end
            match = re.search(r'^(https?://\S+)\s*(?:[\(\[\{]?(\d+)\s*(?:шт|ед|б)?[\)\]\}]?)?', line)
            if match:
                url = match.group(1)
                if match.group(2):
                    try:
                        count = max(1, int(match.group(2)))
                    except ValueError:
                        count = 1

            self.add_row(DiscordLinkItem(url=url, count=count))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if event.modifiers() & Qt.ControlModifier:
                self.validate_and_save()
                return
        super().keyPressEvent(event)

    def validate_and_save(self):
        self.result_items = [r.item for r in self.row_widgets if r.item.url.strip()]
        self.accept()


class EditFieldDialog(QDialog):
    """Dialog to create or edit a field within a department tab."""

    def __init__(self, parent=None, field: Optional[ReportField] = None):
        super().__init__(parent)
        self.field = field
        self.result_field: Optional[ReportField] = None
        self._current_discord_links: List[DiscordLinkItem] = []

        self.setWindowTitle("Настройка поля" if field else "Добавить новое поле")
        self.setFixedWidth(540)
        self.setup_ui()

        if field:
            self.load_field_data(field)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(18, 16, 18, 16)

        # Title
        header = QLabel("🩺 Параметры отчётного поля")
        header.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
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

        # Batch scoring controls (Requirement 5)
        self.batch_mode_chk = QCheckBox("Считать баллами за набор скриншотов (с отбрасыванием остатка)")
        self.batch_mode_chk.setChecked(False)
        self.batch_mode_chk.stateChanged.connect(self.on_batch_mode_toggled)
        folder_layout.addWidget(self.batch_mode_chk)

        self.batch_container = QFrame()
        self.batch_container.setStyleSheet("background-color: #0b1827; border: 1px solid #1a344d; border-radius: 6px; padding: 6px 10px;")
        b_layout = QVBoxLayout(self.batch_container)
        b_layout.setContentsMargins(0, 0, 0, 0)
        b_layout.setSpacing(4)

        b_row = QHBoxLayout()
        b_row.addWidget(QLabel("За каждые:"))
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 999999)
        self.batch_size_spin.setValue(4)
        self.batch_size_spin.setFixedWidth(65)
        b_row.addWidget(self.batch_size_spin)
        b_row.addWidget(QLabel("скриншотов давать:"))

        self.batch_pts_spin = QDoubleSpinBox()
        self.batch_pts_spin.setRange(0.0, 999999.0)
        self.batch_pts_spin.setSingleStep(1.0)
        self.batch_pts_spin.setDecimals(1)
        self.batch_pts_spin.setValue(30.0)
        self.batch_pts_spin.setFixedWidth(75)
        b_row.addWidget(self.batch_pts_spin)
        b_row.addWidget(QLabel("баллов"))
        b_row.addStretch()

        b_hint = QLabel("Пример: 8 скриншотов по 4 шт = 60 б. Остаток (например, 7 шт = 30 б) не учитывается.")
        b_hint.setStyleSheet("font-size: 11px; color: #38bdf8;")

        b_layout.addLayout(b_row)
        b_layout.addWidget(b_hint)
        folder_layout.addWidget(self.batch_container)
        self.batch_container.hide()

        layout.addWidget(self.folder_container)

        # 2. Numeric container (for FieldType.NUMERIC)
        self.numeric_container = QFrame()
        numeric_layout = QVBoxLayout(self.numeric_container)
        numeric_layout.setContentsMargins(0, 0, 0, 0)
        numeric_layout.setSpacing(4)
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
        links_lbl = QLabel("Ссылки на сообщения в Discord:")
        links_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")

        links_btn_row = QHBoxLayout()
        self.config_links_btn = QPushButton("🔗 Настроить ссылки и количество задач...")
        self.config_links_btn.setObjectName("secondaryButton")
        self.config_links_btn.clicked.connect(self.open_links_config_dialog)
        self.links_summary_lbl = QLabel("0 ссылок")
        self.links_summary_lbl.setStyleSheet("color: #a5b4fc; font-weight: 600;")
        links_btn_row.addWidget(self.config_links_btn)
        links_btn_row.addWidget(self.links_summary_lbl)
        links_btn_row.addStretch()

        links_box.addWidget(links_lbl)
        links_box.addLayout(links_btn_row)
        layout.addWidget(self.links_container)
        self.links_container.hide()

        # Standard Points per unit (used for Folder when batch off, Numeric, and Links per task)
        self.points_container = QFrame()
        pts_layout = QVBoxLayout(self.points_container)
        pts_layout.setContentsMargins(0, 0, 0, 0)
        pts_layout.setSpacing(4)
        self.pts_lbl = QLabel("Баллов за 1 скриншот / единицу / задачу:")
        self.pts_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.points_spin = QDoubleSpinBox()
        self.points_spin.setRange(0.0, 1000.0)
        self.points_spin.setSingleStep(0.5)
        self.points_spin.setDecimals(1)
        self.points_spin.setValue(2.0)
        pts_layout.addWidget(self.pts_lbl)
        pts_layout.addWidget(self.points_spin)
        layout.addWidget(self.points_container)

        # Cloud Link (Optional for FOLDER and NUMERIC, hidden for LINKS)
        self.cloud_link_container = QFrame()
        link_layout = QVBoxLayout(self.cloud_link_container)
        link_layout.setContentsMargins(0, 0, 0, 0)
        link_layout.setSpacing(4)
        link_lbl = QLabel("Ссылка на облачное хранилище (Google Диск, Imgur и др., необязательно):")
        link_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.cloud_link_edit = QLineEdit()
        self.cloud_link_edit.setPlaceholderText("https://drive.google.com/drive/folders/... или https://imgur.com/...")
        link_hint = QLabel("Используется при формировании отчёта (не отображается на главном экране)")
        link_hint.setStyleSheet("font-size: 11px; color: #64748b;")
        link_layout.addWidget(link_lbl)
        link_layout.addWidget(self.cloud_link_edit)
        link_layout.addWidget(link_hint)
        layout.addWidget(self.cloud_link_container)

        # Dialog Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        # Connect returnPressed on line edits
        self.name_edit.returnPressed.connect(self.validate_and_save)
        self.folder_edit.returnPressed.connect(self.validate_and_save)
        self.cloud_link_edit.returnPressed.connect(self.validate_and_save)

    def on_batch_mode_toggled(self, state: int):
        checked = self.batch_mode_chk.isChecked()
        if checked:
            self.batch_container.show()
            self.points_container.hide()
        else:
            self.batch_container.hide()
            self.points_container.show()

    def on_type_changed(self, index: int):
        ft = self.type_combo.currentData()
        if ft == FieldType.FOLDER:
            self.folder_container.show()
            self.numeric_container.hide()
            self.links_container.hide()
            self.cloud_link_container.show()
            self.pts_lbl.setText("Баллов за 1 скриншот:")
            self.on_batch_mode_toggled(self.batch_mode_chk.isChecked())
        elif ft == FieldType.NUMERIC:
            self.folder_container.hide()
            self.numeric_container.show()
            self.links_container.hide()
            self.cloud_link_container.show()
            self.points_container.show()
            self.pts_lbl.setText("Баллов за 1 единицу действия:")
        elif ft == FieldType.LINKS:
            self.folder_container.hide()
            self.numeric_container.hide()
            self.links_container.show()
            self.cloud_link_container.hide()
            self.points_container.show()
            self.pts_lbl.setText("Баллов за 1 задачу в ссылке:")

    def choose_folder(self):
        curr = self.folder_edit.text() if os.path.exists(self.folder_edit.text()) else ""
        folder = QFileDialog.getExistingDirectory(self, "Выберите папку со скриншотами", curr)
        if folder:
            self.folder_edit.setText(folder)

    def open_links_config_dialog(self):
        name = self.name_edit.text().strip() or "Ссылки"
        rate = self.points_spin.value()
        dlg = EditLinksDialog(self, field_name=name, items=self._current_discord_links, points_per_unit=rate)
        if dlg.exec():
            self._current_discord_links = dlg.result_items
            self._update_links_summary()

    def _update_links_summary(self):
        cnt = len([it for it in self._current_discord_links if it.url.strip()])
        tot_tasks = sum(it.count for it in self._current_discord_links if it.url.strip())
        self.links_summary_lbl.setText(f"{cnt} ссылок ({tot_tasks} задач)")

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
        self._current_discord_links = f.get_discord_link_items()
        self._update_links_summary()
        self.cloud_link_edit.setText(f.cloud_link or "")

        # Batch mode
        self.batch_mode_chk.setChecked(f.batch_mode_enabled)
        self.batch_size_spin.setValue(f.batch_size)
        self.batch_pts_spin.setValue(f.batch_points)

        self.on_type_changed(idx)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            if isinstance(self.focusWidget(), QPlainTextEdit):
                super().keyPressEvent(event)
                return
            self.validate_and_save()
            return
        super().keyPressEvent(event)

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
        cloud_link = self.cloud_link_edit.text().strip() if ft != FieldType.LINKS else ""

        batch_enabled = self.batch_mode_chk.isChecked() if ft == FieldType.FOLDER else False
        batch_size = self.batch_size_spin.value()
        batch_pts = self.batch_pts_spin.value()

        fid = self.field.id if self.field else str(uuid.uuid4())

        self.result_field = ReportField(
            id=fid,
            name=name,
            field_type=ft,
            folder_path=folder,
            points_per_unit=pts,
            manual_count=manual,
            links=self._current_discord_links if ft == FieldType.LINKS else [],
            batch_mode_enabled=batch_enabled,
            batch_size=batch_size,
            batch_points=batch_pts,
            cloud_link=cloud_link
        )
        self.accept()


class EditTabDialog(QDialog):
    """Dialog to create or edit a tab."""

    def __init__(self, parent=None, tab: Optional[DepartmentTab] = None):
        super().__init__(parent)
        self.tab = tab
        self.result_tab: Optional[DepartmentTab] = None

        self.setWindowTitle("Настройка вкладки" if tab else "Создать новую вкладку")
        self.setFixedWidth(460)
        self.setup_ui()

        if tab:
            self.load_tab_data(tab)

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        header = QLabel("📑 Параметры вкладки")
        header.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        # Title
        title_lbl = QLabel("Название вкладки:")
        title_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Например: Paramedic (PM) или Скорая помощь")
        layout.addWidget(title_lbl)
        layout.addWidget(self.title_edit)

        # Description
        desc_lbl = QLabel("Описание вкладки (необязательно):")
        desc_lbl.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Например: Вызовы, реанимации, отчёты")
        layout.addWidget(desc_lbl)
        layout.addWidget(self.desc_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.setAutoDefault(False)
        self.cancel_btn.clicked.connect(self.reject)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.setObjectName("primaryButton")
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.validate_and_save)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        # Connect returnPressed on line edits
        self.title_edit.returnPressed.connect(self.validate_and_save)
        self.desc_edit.returnPressed.connect(self.validate_and_save)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self.validate_and_save()
            return
        super().keyPressEvent(event)

    def load_tab_data(self, t: DepartmentTab):
        self.title_edit.setText(t.title)
        self.desc_edit.setText(t.description)

    def validate_and_save(self):
        title = self.title_edit.text().strip()
        if not title:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите название вкладки.")
            self.title_edit.setFocus()
            return

        desc = self.desc_edit.text().strip()
        tid = self.tab.id if self.tab else str(uuid.uuid4())
        fields = self.tab.fields if self.tab else []
        code = self.tab.code if self.tab else ""

        self.result_tab = DepartmentTab(
            id=tid,
            title=title,
            code=code,
            description=desc,
            fields=fields
        )
        self.accept()
