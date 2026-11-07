"""Export and Import configuration dialogs for EMS Reporter (Compact & Clean)."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QMessageBox,
    QFrame,
)

from app.models import ReporterConfig, DepartmentTab
from app.storage import ConfigManager


class ExportDialog(QDialog):
    """Compact dialog for choosing export mode (template vs full data) and tab scope."""

    def __init__(self, config: ReporterConfig, active_tab: Optional[DepartmentTab] = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.active_tab = active_tab

        self.setWindowTitle("Экспорт настроек — EMS Reporter")
        self.setFixedWidth(520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Header banner
        header = QFrame()
        header.setStyleSheet(
            "background-color: #0f2234; border: 1px solid #1a3650; border-radius: 6px; padding: 8px 12px;"
        )
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        title = QLabel("📤 Экспорт настроек")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        desc = QLabel("Выберите вариант экспорта для сохранения файла.")
        desc.setStyleSheet("font-size: 11px; color: #94a3b8;")

        h_layout.addWidget(title)
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # Mode Selection (borderless, compact)
        mode_lbl = QLabel("Формат экспорта:")
        mode_lbl.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 12px; margin-top: 4px;")
        layout.addWidget(mode_lbl)

        self.btn_group = QButtonGroup(self)

        # Option 1: Clean Template
        self.radio_template = QRadioButton("Экспорт как шаблон (рекомендуется)")
        self.radio_template.setStyleSheet("font-weight: 600; color: #38bdf8; font-size: 12px;")
        self.radio_template.setChecked(True)
        self.btn_group.addButton(self.radio_template)
        layout.addWidget(self.radio_template)

        template_hint = QLabel("Без путей к файлам, личных ссылок и счётчиков (для отправки другим)")
        template_hint.setStyleSheet("font-size: 11px; color: #94a3b8; margin-left: 20px;")
        layout.addWidget(template_hint)

        # Option 2: Full Data
        self.radio_full = QRadioButton("Экспорт со всеми данными")
        self.radio_full.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px; margin-top: 4px;")
        self.btn_group.addButton(self.radio_full)
        layout.addWidget(self.radio_full)

        full_hint = QLabel("Сохраняет текущие пути к папкам, ссылки, счётчики и профиль")
        full_hint.setStyleSheet("font-size: 11px; color: #94a3b8; margin-left: 20px;")
        layout.addWidget(full_hint)

        # Scope Checkbox (borderless, compact)
        tab_title = self.active_tab.title if self.active_tab else "активную"
        self.chk_active_only = QCheckBox(f"Экспортировать только текущую вкладку («{tab_title}»)")
        self.chk_active_only.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px; margin-top: 8px;")
        self.chk_active_only.setChecked(False)
        layout.addWidget(self.chk_active_only)

        layout.addSpacing(6)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.export_btn = QPushButton("💾 Выбрать файл и сохранить...")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.setDefault(True)
        self.export_btn.clicked.connect(self.perform_export)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.export_btn)
        layout.addLayout(btn_layout)

    def perform_export(self):
        is_template = self.radio_template.isChecked()
        active_only = self.chk_active_only.isChecked()

        if active_only and self.active_tab:
            safe_title = "".join(c for c in self.active_tab.title if c.isalnum() or c in (" ", "_", "-")).strip()
            if is_template:
                default_name = f"Шаблон_{safe_title}.json"
            else:
                default_name = f"Настройки_{safe_title}.json"
        else:
            if is_template:
                default_name = "Шаблон_EMS_все_вкладки.json"
            else:
                default_name = "ems_preset_settings.json"

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить файл настроек EMS Reporter",
            default_name,
            "JSON files (*.json);;All files (*.*)"
        )
        if not path:
            return

        try:
            active_id = self.active_tab.id if self.active_tab else None
            export_cfg = self.config.create_export_copy(
                as_template=is_template,
                active_tab_only=active_only,
                active_tab_id=active_id
            )
            ConfigManager.export_to_file(export_cfg, path)

            mode_str = "как чистый шаблон" if is_template else "со всеми данными"
            scope_str = f"вкладки «{self.active_tab.title}»" if (active_only and self.active_tab) else f"всех вкладок ({len(export_cfg.tabs)} шт.)"

            QMessageBox.information(
                self,
                "Экспорт завершён",
                f"Настройки успешно сохранены {mode_str} для {scope_str}:\n{path}"
            )
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка экспорта", f"Не удалось сохранить файл:\n{e}")


class ImportOptionsDialog(QDialog):
    """Compact dialog for choosing import strategy (append vs replace)."""

    def __init__(self, filename: str, imported_config: ReporterConfig, current_tabs_count: int, parent=None):
        super().__init__(parent)
        self.filename = filename
        self.imported_config = imported_config
        self.current_tabs_count = current_tabs_count
        self.selected_mode: str = "append"
        self.should_update_profile: bool = False

        self.setWindowTitle("Параметры импорта — EMS Reporter")
        self.setFixedWidth(520)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(8)

        # Header banner
        header = QFrame()
        header.setStyleSheet(
            "background-color: #0f2234; border: 1px solid #1a3650; border-radius: 6px; padding: 8px 12px;"
        )
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(2)

        title = QLabel("📥 Параметры импорта")
        title.setStyleSheet("font-size: 14px; font-weight: bold; color: #38bdf8;")
        desc = QLabel(f"Файл: {Path(self.filename).name}")
        desc.setStyleSheet("font-size: 11px; color: #94a3b8;")

        h_layout.addWidget(title)
        h_layout.addWidget(desc)
        layout.addWidget(header)

        # File contents info (compact)
        tab_cnt = len(self.imported_config.tabs)
        tab_names = ", ".join([f"«{t.title}»" for t in self.imported_config.tabs]) or "нет вкладок"

        info_lbl = QLabel(f"Найдено вкладок: <b>{tab_cnt}</b> ({tab_names})")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px; margin-top: 2px;")
        layout.addWidget(info_lbl)

        # Mode Selection (borderless, compact)
        mode_lbl = QLabel("Способ импорта:")
        mode_lbl.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 12px; margin-top: 4px;")
        layout.addWidget(mode_lbl)

        self.btn_group = QButtonGroup(self)

        # Option 1: Append
        self.radio_append = QRadioButton("Добавить к существующим вкладкам")
        self.radio_append.setStyleSheet("font-weight: 600; color: #10b981; font-size: 12px;")
        self.radio_append.setChecked(self.current_tabs_count > 0)
        self.btn_group.addButton(self.radio_append)
        layout.addWidget(self.radio_append)

        append_hint = QLabel("Текущие вкладки сохранятся, новые добавятся в конец списка")
        append_hint.setStyleSheet("font-size: 11px; color: #94a3b8; margin-left: 20px;")
        layout.addWidget(append_hint)

        # Option 2: Replace
        self.radio_replace = QRadioButton("Заменить существующие вкладки")
        self.radio_replace.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px; margin-top: 4px;")
        if self.current_tabs_count == 0:
            self.radio_replace.setChecked(True)
        self.btn_group.addButton(self.radio_replace)
        layout.addWidget(self.radio_replace)

        replace_hint = QLabel("Все текущие вкладки будут удалены и заменены новыми из файла")
        replace_hint.setStyleSheet("font-size: 11px; color: #f87171; margin-left: 20px;")
        layout.addWidget(replace_hint)

        # Optional Profile Update Checkbox
        has_profile = bool(self.imported_config.player_name or self.imported_config.player_static)
        self.chk_profile = QCheckBox("Обновить также имя сотрудника и статик из файла")
        self.chk_profile.setStyleSheet("font-weight: 600; color: #cbd5e1; font-size: 12px; margin-top: 8px;")
        self.chk_profile.setChecked(has_profile and self.current_tabs_count == 0)
        if not has_profile:
            self.chk_profile.setEnabled(False)
            self.chk_profile.setText("В файле нет данных сотрудника")
        layout.addWidget(self.chk_profile)

        layout.addSpacing(6)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.import_btn = QPushButton("📥 Импортировать")
        self.import_btn.setObjectName("primaryButton")
        self.import_btn.setDefault(True)
        self.import_btn.clicked.connect(self.perform_import)

        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.import_btn)
        layout.addLayout(btn_layout)

    def perform_import(self):
        self.selected_mode = "append" if self.radio_append.isChecked() else "replace"
        self.should_update_profile = self.chk_profile.isChecked()
        self.accept()
