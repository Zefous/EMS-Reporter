"""Report Preview and Export Dialog with individual fields (no quotes, multi-line support)."""

from __future__ import annotations

from typing import Optional, List
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QCheckBox,
    QApplication,
    QMessageBox,
    QFileDialog,
    QScrollArea,
    QFrame,
)

from app.models import ReporterConfig, DepartmentTab


class ReportFieldItem(QWidget):
    """Single report item with a title label, editable/copyable value, and a copy button."""

    def __init__(self, title: str, value: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value.strip()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 8)
        layout.setSpacing(4)

        # Field title label
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("font-weight: 700; color: #38bdf8; font-size: 13px;")
        layout.addWidget(self.title_lbl)

        # Value input row
        row = QHBoxLayout()
        row.setSpacing(8)

        if "\n" in self.value:
            self.editor = QPlainTextEdit(self.value)
            line_cnt = len(self.value.splitlines())
            h = min(180, max(65, line_cnt * 20 + 22))
            self.editor.setFixedHeight(h)
            self.editor.setStyleSheet(
                "font-family: 'Consolas', monospace; font-size: 12px; padding: 6px 10px; background-color: #07101b;"
            )
            row.addWidget(self.editor, 1)
        else:
            self.editor = QLineEdit(self.value)
            self.editor.setStyleSheet("font-size: 13px; padding: 6px 10px; background-color: #07101b;")
            row.addWidget(self.editor, 1)

        self.copy_btn = QPushButton("📋 Скопировать")
        self.copy_btn.setObjectName("secondaryButton")
        self.copy_btn.setFixedWidth(130)
        self.copy_btn.clicked.connect(self.copy_value)

        row.addWidget(self.copy_btn)
        layout.addLayout(row)

    def get_text(self) -> str:
        if isinstance(self.editor, QPlainTextEdit):
            return self.editor.toPlainText().strip()
        return self.editor.text().strip()

    def set_text(self, text: str):
        self.value = text.strip()
        if isinstance(self.editor, QPlainTextEdit):
            self.editor.setPlainText(self.value)
        else:
            self.editor.setText(self.value)

    def copy_value(self):
        text = self.get_text()
        QApplication.clipboard().setText(text)
        self.copy_btn.setText("✓ Скопировано!")
        self.copy_btn.setStyleSheet("background-color: #059669; color: white;")
        QTimer.singleShot(1500, self.reset_copy_btn)

    def reset_copy_btn(self):
        self.copy_btn.setText("📋 Скопировать")
        self.copy_btn.setStyleSheet("")


class ReportPreviewDialog(QDialog):
    """Dialog showing the department report as individual form fields without quotes."""

    def __init__(
        self,
        config: ReporterConfig,
        tab: Optional[DepartmentTab] = None,
        current_tab_id: Optional[str] = None,
        parent=None
    ):
        super().__init__(parent)
        self.config = config

        # Determine target department tab
        self.tab = tab
        if self.tab is None and current_tab_id:
            self.tab = next((t for t in config.tabs if t.id == current_tab_id), None)
        if self.tab is None and config.active_tab_id:
            self.tab = next((t for t in config.tabs if t.id == config.active_tab_id), None)
        if self.tab is None and config.tabs:
            self.tab = config.tabs[0]

        tab_name = self.tab.title if self.tab else "Вкладка"
        self.setWindowTitle(f"🚑 Отчёт по: {tab_name}")
        self.resize(780, 620)
        self.setMinimumSize(600, 460)

        self.field_items: List[ReportFieldItem] = []
        self.setup_ui()
        self.populate_fields()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header banner
        header_frame = QFrame()
        header_frame.setStyleSheet(
            "background-color: #0f2234; border: 1px solid #1a3650; border-radius: 8px; padding: 10px 16px;"
        )
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        tab_title = self.tab.title if self.tab else "Не выбрана"
        title_lbl = QLabel(f"📋 Отчёт по: {tab_title}")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")

        desc_lbl = QLabel(
            "Поля отчёта созданы автоматически на основе настроек вкладки. "
            "Вы можете скопировать каждое поле отдельно для формы или весь отчёт целиком."
        )
        desc_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")

        h_layout.addWidget(title_lbl)
        h_layout.addWidget(desc_lbl)
        layout.addWidget(header_frame)

        # Options row
        opt_layout = QHBoxLayout()
        self.newline_links_chk = QCheckBox("Несколько ссылок выводить построчно (каждая с новой строки)")
        self.newline_links_chk.setChecked(True)
        self.newline_links_chk.stateChanged.connect(self.populate_fields)
        opt_layout.addWidget(self.newline_links_chk)
        opt_layout.addStretch()
        layout.addLayout(opt_layout)

        # Scroll Area for fields
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.scroll_content = QWidget()
        self.items_layout = QVBoxLayout(self.scroll_content)
        self.items_layout.setContentsMargins(8, 8, 8, 8)
        self.items_layout.setSpacing(10)

        self.scroll.setWidget(self.scroll_content)
        layout.addWidget(self.scroll, 1)

        # Footer
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        self.status_msg_lbl = QLabel("")
        self.status_msg_lbl.setStyleSheet("color: #10b981; font-weight: 600;")
        footer_layout.addWidget(self.status_msg_lbl, 1)

        self.copy_all_btn = QPushButton("📋 Скопировать весь отчёт")
        self.copy_all_btn.setObjectName("primaryButton")
        self.copy_all_btn.clicked.connect(self.copy_all_report)

        self.save_txt_btn = QPushButton("💾 Сохранить в .txt")
        self.save_txt_btn.setObjectName("secondaryButton")
        self.save_txt_btn.clicked.connect(self.save_to_txt)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setObjectName("secondaryButton")
        self.close_btn.clicked.connect(self.accept)

        footer_layout.addWidget(self.copy_all_btn)
        footer_layout.addWidget(self.save_txt_btn)
        footer_layout.addWidget(self.close_btn)
        layout.addLayout(footer_layout)

    def populate_fields(self):
        """Build all report fields for current department without quotes."""
        # Clear existing
        for item in self.field_items:
            self.items_layout.removeWidget(item)
            item.deleteLater()
        self.field_items.clear()

        join_nl = self.newline_links_chk.isChecked()

        # 1. First Field: Player Name | Static ID
        name = self.config.player_name.strip() if self.config.player_name else ""
        static = self.config.player_static.strip() if self.config.player_static else ""
        if name and static:
            player_info = f"{name} | {static}"
        elif name:
            player_info = name
        elif static:
            player_info = static
        else:
            player_info = "Имя Фамилия | статик"

        first_item = ReportFieldItem("Имя Фамилия | статик", player_info, self.scroll_content)
        self.items_layout.addWidget(first_item)
        self.field_items.append(first_item)

        # 2. Intermediate Fields from the active tab
        if self.tab and self.tab.fields:
            for field in self.tab.fields:
                entry_val = field.format_report_entry(join_with_newline=join_nl)
                item = ReportFieldItem(field.name, entry_val, self.scroll_content)
                self.items_layout.addWidget(item)
                self.field_items.append(item)
        else:
            empty_lbl = QLabel("В этой вкладке пока нет полей. Добавьте поля на главном окне.")
            empty_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 12px;")
            self.items_layout.addWidget(empty_lbl)

        # 3. Last Field: Total Points of active tab
        tot_pts = self.tab.total_points() if self.tab else 0.0
        pts_str = f"{int(tot_pts)}" if tot_pts.is_integer() else f"{tot_pts:.1f}"

        last_item = ReportFieldItem("Общее количество баллов", pts_str, self.scroll_content)
        self.items_layout.addWidget(last_item)
        self.field_items.append(last_item)

        self.items_layout.addStretch()

    def assemble_full_report_text(self) -> str:
        """Assemble full report text in plain format (no quotes):
        Title 1
        Value 1
        Title 2
        Value 2
        ...
        """
        lines = []
        for item in self.field_items:
            lines.append(item.title)
            lines.append(item.get_text())
        return "\n".join(lines)

    def copy_all_report(self):
        text = self.assemble_full_report_text()
        QApplication.clipboard().setText(text)
        self.status_msg_lbl.setText("✓ Весь отчёт скопирован в буфер обмена!")

    def save_to_txt(self):
        safe_title = "".join(c for c in (self.tab.title if self.tab else "EMS") if c.isalnum() or c in (" ", "_", "-")).strip()
        default_filename = f"Отчёт_{safe_title}.txt"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в текстовый файл",
            default_filename,
            "Text files (*.txt);;All files (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.assemble_full_report_text())
                QMessageBox.information(self, "Успех", f"Отчёт успешно сохранён:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
