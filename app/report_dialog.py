"""Report Preview and Export Dialog."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QCheckBox,
    QApplication,
    QMessageBox,
    QFileDialog,
)

from app.models import ReporterConfig
from app.storage import ReportGenerator


class ReportPreviewDialog(QDialog):
    """Dialog showing the formatted Discord/Forum report ready to be copied or saved."""

    def __init__(self, config: ReporterConfig, current_tab_id: str | None = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.current_tab_id = current_tab_id

        self.setWindowTitle("🚑 Готовый отчёт EMS - Majestic RP")
        self.resize(720, 600)
        self.setup_ui()
        self.update_report_text()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        # Header
        header = QLabel("📋 Сформированный отчёт для Discord / Форума")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #38bdf8;")
        layout.addWidget(header)

        # Options row
        opt_layout = QHBoxLayout()
        self.active_only_chk = QCheckBox("Включить только текущий отдел (активную вкладку)")
        self.active_only_chk.stateChanged.connect(self.update_report_text)
        opt_layout.addWidget(self.active_only_chk)
        opt_layout.addStretch()
        layout.addLayout(opt_layout)

        # Report text editor
        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(False)  # User can make manual edits if desired
        self.text_edit.setStyleSheet(
            "font-family: 'Consolas', 'Courier New', monospace; font-size: 12px; line-height: 1.4;"
        )
        layout.addWidget(self.text_edit, 1)

        # Footer action buttons
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(10)

        self.status_msg_lbl = QLabel("")
        self.status_msg_lbl.setStyleSheet("color: #10b981; font-weight: 600;")
        footer_layout.addWidget(self.status_msg_lbl, 1)

        self.save_txt_btn = QPushButton("💾 Сохранить в .txt")
        self.save_txt_btn.setObjectName("secondaryButton")
        self.save_txt_btn.clicked.connect(self.save_to_txt)

        self.copy_btn = QPushButton("📋 Скопировать в буфер")
        self.copy_btn.setObjectName("primaryButton")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setObjectName("secondaryButton")
        self.close_btn.clicked.connect(self.accept)

        footer_layout.addWidget(self.save_txt_btn)
        footer_layout.addWidget(self.copy_btn)
        footer_layout.addWidget(self.close_btn)
        layout.addLayout(footer_layout)

    def update_report_text(self):
        active_only = self.active_only_chk.isChecked()
        text = ReportGenerator.generate_markdown_report(
            self.config,
            active_tab_only=active_only,
            current_tab_id=self.current_tab_id
        )
        self.text_edit.setPlainText(text)

    def copy_to_clipboard(self):
        text = self.text_edit.toPlainText()
        QApplication.clipboard().setText(text)
        self.status_msg_lbl.setText("✓ Отчёт успешно скопирован в буфер обмена!")

    def save_to_txt(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить отчёт в текстовый файл",
            "EMS_Report.txt",
            "Text files (*.txt);;All files (*.*)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self.text_edit.toPlainText())
                QMessageBox.information(self, "Успех", f"Отчёт успешно сохранён:\n{path}")
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить файл:\n{e}")
