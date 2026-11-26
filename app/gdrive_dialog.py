"""Google Drive upload and sync dialog for EMS Reporter."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QProgressBar,
    QFrame,
    QMessageBox,
    QFileDialog,
)

from app.models import DepartmentTab, FieldType, ReportField, ReporterConfig
from app.gdrive import GoogleDriveClient, SyncPlan, find_client_secrets, plan_sync, format_gdrive_error


@dataclass
class FieldSyncTask:
    field: ReportField
    local_files: List[Path]
    subfolder: Dict[str, Any]
    plan: SyncPlan


class GDriveAuthThread(QThread):
    """Background thread for OAuth 2.0 browser authentication."""
    finished_auth = Signal(object, str)  # user_info dict or None, error_msg

    def __init__(self, client: GoogleDriveClient, secrets_path: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.client = client
        self.secrets_path = secrets_path

    def run(self):
        try:
            user_info = self.client.authenticate(self.secrets_path)
            self.finished_auth.emit(user_info, "")
        except Exception as e:
            self.finished_auth.emit(None, format_gdrive_error(e))


class GDriveListFoldersThread(QThread):
    """Background thread to fetch existing report folders from Google Drive."""
    finished_list = Signal(list, str)  # folders list, error_msg

    def __init__(self, client: GoogleDriveClient, parent=None):
        super().__init__(parent)
        self.client = client

    def run(self):
        try:
            folders = self.client.list_report_folders()
            self.finished_list.emit(folders, "")
        except Exception as e:
            self.finished_list.emit([], format_gdrive_error(e))


class GDrivePrepareThread(QThread):
    """Background thread to create/open report folder and compute sync plans."""
    progress = Signal(str)
    finished_prepare = Signal(object, list, str)  # report_folder, List[FieldSyncTask], error_msg

    def __init__(
        self,
        client: GoogleDriveClient,
        fields: List[ReportField],
        create_new: bool,
        new_folder_name: str,
        existing_folder: Optional[Dict[str, Any]] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.fields = fields
        self.create_new = create_new
        self.new_folder_name = new_folder_name
        self.existing_folder = existing_folder

    def run(self):
        try:
            if self.create_new:
                self.progress.emit("Проверка свободного места на Google Диске...")
                all_local = [p for f in self.fields for p in f.get_local_image_files()]
                quota_err = self.client.check_quota_for_files(all_local)
                if quota_err:
                    self.finished_prepare.emit(None, [], quota_err)
                    return

                self.progress.emit(f"Создание папки «{self.new_folder_name}»...")
                report_folder = self.client.create_unique_report_folder(self.new_folder_name)
            else:
                report_folder = self.existing_folder
                if not report_folder or not report_folder.get("id"):
                    raise ValueError("Не выбрана существующая папка на Google Диске.")

            tasks: List[FieldSyncTask] = []
            for f in self.fields:
                local_files = f.get_local_image_files()
                if not local_files and self.create_new:
                    continue

                self.progress.emit(f"Проверка папки поля «{f.name}»...")
                subfolder = self.client.get_or_create_subfolder(report_folder["id"], f.name)
                remote_files = self.client.list_files_in_folder(subfolder["id"])
                sync_plan = plan_sync(local_files, remote_files)
                tasks.append(FieldSyncTask(field=f, local_files=local_files, subfolder=subfolder, plan=sync_plan))

            if not self.create_new:
                self.progress.emit("Проверка свободного места на Google Диске...")
                new_files = [p for t in tasks for p in t.plan.to_upload]
                quota_err = self.client.check_quota_for_files(new_files)
                if quota_err:
                    self.finished_prepare.emit(None, [], quota_err)
                    return

            self.finished_prepare.emit(report_folder, tasks, "")
        except Exception as e:
            self.finished_prepare.emit(None, [], format_gdrive_error(e))


class GDriveExecuteThread(QThread):
    """Background thread to delete orphaned files (if confirmed) and upload new files."""
    progress = Signal(int, int, str)  # current, total, status_text
    finished_execute = Signal(dict, str)  # summary dict, error_msg

    def __init__(
        self,
        client: GoogleDriveClient,
        tasks: List[FieldSyncTask],
        delete_orphans: bool,
        parent=None,
    ):
        super().__init__(parent)
        self.client = client
        self.tasks = tasks
        self.delete_orphans = delete_orphans

    def run(self):
        try:
            total_uploads = sum(len(t.plan.to_upload) for t in self.tasks)
            total_deletes = sum(len(t.plan.orphaned_remote) for t in self.tasks) if self.delete_orphans else 0
            total_ops = max(1, total_uploads + total_deletes)
            done_ops = 0

            uploaded_count = 0
            skipped_count = sum(len(t.plan.already_synced) for t in self.tasks)
            deleted_count = 0
            field_links: Dict[str, str] = {}

            for t in self.tasks:
                link = t.subfolder.get("webViewLink") or f"https://drive.google.com/drive/folders/{t.subfolder['id']}"
                field_links[t.field.id] = link

                if self.delete_orphans:
                    for rf in t.plan.orphaned_remote:
                        self.progress.emit(done_ops, total_ops, f"Удаление из облака: {rf.get('name', '')}...")
                        self.client.delete_file(rf["id"])
                        deleted_count += 1
                        done_ops += 1

                for lp in t.plan.to_upload:
                    self.progress.emit(done_ops, total_ops, f"Загрузка ({t.field.name}): {lp.name}...")
                    self.client.upload_file(t.subfolder["id"], lp)
                    uploaded_count += 1
                    done_ops += 1

            self.progress.emit(total_ops, total_ops, "Готово!")
            self.finished_execute.emit(
                {
                    "uploaded": uploaded_count,
                    "skipped": skipped_count,
                    "deleted": deleted_count,
                    "field_links": field_links,
                },
                "",
            )
        except Exception as e:
            self.finished_execute.emit({}, format_gdrive_error(e))


class GoogleDriveUploadDialog(QDialog):
    """Dialog for authenticating with Google Drive and uploading/syncing tab screenshots."""

    def __init__(
        self,
        config: ReporterConfig,
        tab: DepartmentTab,
        client: Optional[GoogleDriveClient] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.config = config
        self.tab = tab
        self.client = client or GoogleDriveClient()
        self.custom_secrets_path: Optional[str] = None
        self.links_updated = False
        self._existing_folders: List[Dict[str, Any]] = []
        self._last_report_folder: Optional[Dict[str, Any]] = None

        self._auth_thread: Optional[GDriveAuthThread] = None
        self._list_thread: Optional[GDriveListFoldersThread] = None
        self._prepare_thread: Optional[GDrivePrepareThread] = None
        self._execute_thread: Optional[GDriveExecuteThread] = None

        self.setWindowTitle(f"☁️ Выгрузка на Google Диск — {tab.title}")
        self.setFixedWidth(560)
        self.setup_ui()
        self.refresh_auth_state()

    def get_eligible_fields(self) -> List[ReportField]:
        """Return fields in the active tab that support folder screenshot uploads."""
        return [
            f for f in self.tab.fields
            if f.field_type in (FieldType.FOLDER, FieldType.NUMERIC_WITH_FOLDER)
            and f.folder_path.strip()
        ]

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel(f"☁️ Выгрузка скриншотов на Google Диск")
        header.setStyleSheet("font-size: 15px; font-weight: 700; color: #38bdf8;")
        layout.addWidget(header)

        # 1. Account Card
        acc_frame = QFrame()
        acc_frame.setObjectName("accFrame")
        acc_frame.setStyleSheet("#accFrame { background-color: #0f2234; border: 1px solid #1a3650; border-radius: 6px; }")
        acc_layout = QHBoxLayout(acc_frame)
        acc_layout.setContentsMargins(12, 8, 12, 8)
        acc_layout.setSpacing(8)

        self.auth_status_lbl = QLabel("Проверка авторизации...")
        self.auth_status_lbl.setStyleSheet("font-size: 12px; color: #cbd5e1;")

        self.secrets_btn = QPushButton("📄 Ключ...")
        self.secrets_btn.setObjectName("secondaryButton")
        self.secrets_btn.setToolTip("Указать свой файл client_secrets.json (если не встроен)")
        self.secrets_btn.clicked.connect(self.pick_client_secrets)

        self.auth_btn = QPushButton("🔑 Войти в Google")
        self.auth_btn.setObjectName("primaryButton")
        self.auth_btn.clicked.connect(self.on_auth_clicked)

        acc_layout.addWidget(self.auth_status_lbl, 1)
        acc_layout.addWidget(self.secrets_btn)
        acc_layout.addWidget(self.auth_btn)
        layout.addWidget(acc_frame)

        # 2. Target Folder Selection
        folder_frame = QFrame()
        folder_frame.setObjectName("folderFrame")
        folder_frame.setStyleSheet("#folderFrame { background-color: #0d1a29; border: 1px solid #162a3f; border-radius: 6px; }")
        f_layout = QVBoxLayout(folder_frame)
        f_layout.setContentsMargins(12, 10, 12, 10)
        f_layout.setSpacing(8)

        f_title = QLabel("Целевая папка отчёта на Google Диске:")
        f_title.setStyleSheet("font-weight: 600; color: #cbd5e1;")
        f_layout.addWidget(f_title)

        self.mode_group = QButtonGroup(self)
        self.radio_new = QRadioButton("Создать новую папку")
        self.radio_existing = QRadioButton("Обновить существующую папку")
        self.radio_new.setChecked(True)
        self.mode_group.addButton(self.radio_new)
        self.mode_group.addButton(self.radio_existing)
        self.radio_new.toggled.connect(self.on_mode_toggled)

        default_name = f"{self.tab.title} — {datetime.now().strftime('%d.%m.%Y')}"
        self.new_name_edit = QLineEdit(default_name)
        self.new_name_edit.setPlaceholderText("Название папки на Google Диске")

        existing_row = QHBoxLayout()
        existing_row.setSpacing(6)
        self.existing_combo = QComboBox()
        self.existing_combo.setEnabled(False)
        self.refresh_folders_btn = QPushButton("🔄")
        self.refresh_folders_btn.setObjectName("iconButton")
        self.refresh_folders_btn.setFixedSize(28, 28)
        self.refresh_folders_btn.setToolTip("Обновить список папок с Google Диска")
        self.refresh_folders_btn.setEnabled(False)
        self.refresh_folders_btn.clicked.connect(self.load_existing_folders)
        existing_row.addWidget(self.existing_combo, 1)
        existing_row.addWidget(self.refresh_folders_btn)

        f_layout.addWidget(self.radio_new)
        f_layout.addWidget(self.new_name_edit)
        f_layout.addWidget(self.radio_existing)
        f_layout.addLayout(existing_row)
        layout.addWidget(folder_frame)

        # 3. Options & Fields Summary
        self.auto_bind_chk = QCheckBox("Автоматически привязать ссылки Google Диска к полям отчёта")
        self.auto_bind_chk.setChecked(self.config.auto_bind_gdrive_links)
        self.auto_bind_chk.stateChanged.connect(self.on_auto_bind_changed)
        layout.addWidget(self.auto_bind_chk)

        eligible = self.get_eligible_fields()
        total_files = sum(len(f.get_local_image_files()) for f in eligible)
        self.summary_lbl = QLabel(
            f"Вкладка «{self.tab.title}»: найдено полей с папками — {len(eligible)}, "
            f"всего скриншотов — {total_files} шт."
        )
        self.summary_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")
        self.summary_lbl.setWordWrap(True)
        layout.addWidget(self.summary_lbl)

        # 4. Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.status_lbl = QLabel("")
        self.status_lbl.setStyleSheet("font-size: 11px; color: #38bdf8;")
        self.status_lbl.hide()

        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_lbl)

        # 5. Bottom Buttons
        btn_row = QHBoxLayout()
        self.open_folder_btn = QPushButton("🌐 Открыть папку на Диске")
        self.open_folder_btn.setObjectName("secondaryButton")
        self.open_folder_btn.hide()
        self.open_folder_btn.clicked.connect(self.open_last_folder_in_browser)

        btn_row.addWidget(self.open_folder_btn)
        btn_row.addStretch()

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setObjectName("secondaryButton")
        self.close_btn.clicked.connect(self.reject)

        self.upload_btn = QPushButton("☁️ Начать выгрузку")
        self.upload_btn.setObjectName("successButton")
        self.upload_btn.clicked.connect(self.start_upload)

        btn_row.addWidget(self.close_btn)
        btn_row.addWidget(self.upload_btn)
        layout.addLayout(btn_row)

    def on_auto_bind_changed(self):
        self.config.auto_bind_gdrive_links = self.auto_bind_chk.isChecked()

    def on_mode_toggled(self):
        is_new = self.radio_new.isChecked()
        self.new_name_edit.setEnabled(is_new)
        self.existing_combo.setEnabled(not is_new)
        self.refresh_folders_btn.setEnabled(not is_new)
        if not is_new and not self._existing_folders and self.client.is_authenticated():
            self.load_existing_folders()

    def refresh_auth_state(self):
        authed = self.client.is_authenticated()
        if authed:
            info = self.client.get_user_info()
            email = (info or {}).get("emailAddress") or "Google-аккаунт"
            self.auth_status_lbl.setText(f"✅ Подключён: {email}")
            self.auth_status_lbl.setStyleSheet("font-size: 12px; color: #34d399; font-weight: 600;")
            self.auth_btn.setText("Выйти")
            self.auth_btn.setObjectName("secondaryButton")
            self.secrets_btn.hide()
            self.upload_btn.setEnabled(len(self.get_eligible_fields()) > 0)
        else:
            self.auth_status_lbl.setText("🔒 Не выполнен вход в Google")
            self.auth_status_lbl.setStyleSheet("font-size: 12px; color: #94a3b8;")
            self.auth_btn.setText("🔑 Войти в Google")
            self.auth_btn.setObjectName("primaryButton")
            self.secrets_btn.setVisible(find_client_secrets(self.custom_secrets_path) is None)
            self.upload_btn.setEnabled(False)
        self.auth_btn.style().unpolish(self.auth_btn)
        self.auth_btn.style().polish(self.auth_btn)

    def pick_client_secrets(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл client_secrets.json",
            "",
            "JSON files (*.json);;All files (*.*)",
        )
        if path:
            self.custom_secrets_path = path
            self.refresh_auth_state()

    def on_auth_clicked(self):
        if self.client.is_authenticated():
            self.client.logout()
            self._existing_folders = []
            self.existing_combo.clear()
            self.refresh_auth_state()
            return

        if not find_client_secrets(self.custom_secrets_path):
            QMessageBox.warning(
                self,
                "Нет файла client_secrets.json",
                "Для входа в Google необходим файл client_secrets.json.\n"
                "Нажмите «📄 Ключ...» и выберите файл, либо положите его рядом с программой.",
            )
            return

        self.auth_btn.setEnabled(False)
        self.auth_status_lbl.setText("⏳ Ожидание входа в браузере...")
        self._auth_thread = GDriveAuthThread(self.client, self.custom_secrets_path, parent=self)
        self._auth_thread.finished_auth.connect(self.on_auth_finished)
        self._auth_thread.start()

    def on_auth_finished(self, user_info, error_msg: str):
        self.auth_btn.setEnabled(True)
        if error_msg:
            QMessageBox.warning(self, "Ошибка авторизации", f"Не удалось войти в Google:\n{error_msg}")
        self.refresh_auth_state()
        if self.radio_existing.isChecked() and self.client.is_authenticated():
            self.load_existing_folders()

    def load_existing_folders(self):
        if not self.client.is_authenticated():
            return
        self.refresh_folders_btn.setEnabled(False)
        self.existing_combo.clear()
        self.existing_combo.addItem("Загрузка списка папок...", None)
        self._list_thread = GDriveListFoldersThread(self.client, parent=self)
        self._list_thread.finished_list.connect(self.on_folders_loaded)
        self._list_thread.start()

    def on_folders_loaded(self, folders: list, error_msg: str):
        self.refresh_folders_btn.setEnabled(self.radio_existing.isChecked())
        self.existing_combo.clear()
        if error_msg:
            self.existing_combo.addItem("Ошибка загрузки папок", None)
            QMessageBox.warning(self, "Google Диск", f"Не удалось получить список папок:\n{error_msg}")
            return

        self._existing_folders = folders
        if not folders:
            self.existing_combo.addItem("Ранее созданные папки не найдены", None)
            return

        for f in folders:
            self.existing_combo.addItem(f.get("name", "Без названия"), f)

    def _set_busy(self, busy: bool):
        self.upload_btn.setEnabled(not busy)
        self.auth_btn.setEnabled(not busy)
        self.radio_new.setEnabled(not busy)
        self.radio_existing.setEnabled(not busy)
        self.new_name_edit.setEnabled(not busy and self.radio_new.isChecked())
        self.existing_combo.setEnabled(not busy and self.radio_existing.isChecked())
        self.refresh_folders_btn.setEnabled(not busy and self.radio_existing.isChecked())

    def start_upload(self):
        eligible = self.get_eligible_fields()
        if not eligible:
            QMessageBox.information(self, "Выгрузка", "В текущей вкладке нет полей с привязанными папками.")
            return

        create_new = self.radio_new.isChecked()
        new_name = self.new_name_edit.text().strip()
        existing_folder = self.existing_combo.currentData() if not create_new else None

        if create_new and not new_name:
            QMessageBox.warning(self, "Внимание", "Укажите название новой папки.")
            self.new_name_edit.setFocus()
            return
        if not create_new and not existing_folder:
            QMessageBox.warning(self, "Внимание", "Выберите существующую папку на Google Диске.")
            return

        self._set_busy(True)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.show()
        self.status_lbl.setText("Подготовка и сверка файлов...")
        self.status_lbl.show()

        self._prepare_thread = GDrivePrepareThread(
            client=self.client,
            fields=eligible,
            create_new=create_new,
            new_folder_name=new_name,
            existing_folder=existing_folder,
            parent=self,
        )
        self._prepare_thread.progress.connect(self.status_lbl.setText)
        self._prepare_thread.finished_prepare.connect(self.on_prepare_finished)
        self._prepare_thread.start()

    def on_prepare_finished(self, report_folder, tasks: List[FieldSyncTask], error_msg: str):
        if error_msg:
            self._set_busy(False)
            self.progress_bar.hide()
            self.status_lbl.hide()
            QMessageBox.warning(self, "Ошибка подготовки", f"Не удалось подготовить выгрузку:\n{error_msg}")
            return

        self._last_report_folder = report_folder

        if not tasks:
            self._set_busy(False)
            self.progress_bar.hide()
            self.status_lbl.hide()
            QMessageBox.information(self, "Выгрузка", "В выбранных папках нет скриншотов для загрузки.")
            return

        # Check for orphaned remote files (deleted locally, still in cloud)
        orphan_lines: List[str] = []
        for t in tasks:
            if t.plan.orphaned_remote:
                names = ", ".join(rf.get("name", "?") for rf in t.plan.orphaned_remote[:10])
                extra = f" и ещё {len(t.plan.orphaned_remote) - 10}" if len(t.plan.orphaned_remote) > 10 else ""
                orphan_lines.append(f"• {t.field.name}: {names}{extra}")

        delete_orphans = False
        if orphan_lines:
            msg = (
                "В локальных папках были удалены следующие файлы, но они остались в облаке:\n\n"
                + "\n".join(orphan_lines)
                + "\n\nУдалить эти файлы из Google Диска?"
            )
            reply = QMessageBox.question(
                self,
                "Удалённые локально файлы",
                msg,
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            delete_orphans = reply == QMessageBox.Yes

        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self._execute_thread = GDriveExecuteThread(
            client=self.client,
            tasks=tasks,
            delete_orphans=delete_orphans,
            parent=self,
        )
        self._execute_thread.progress.connect(self.on_execute_progress)
        self._execute_thread.finished_execute.connect(self.on_execute_finished)
        self._execute_thread.start()

    def on_execute_progress(self, current: int, total: int, text: str):
        pct = int((current / max(1, total)) * 100)
        self.progress_bar.setValue(pct)
        self.status_lbl.setText(text)

    def on_execute_finished(self, summary: dict, error_msg: str):
        self._set_busy(False)
        if error_msg:
            self.progress_bar.hide()
            self.status_lbl.setText("Ошибка при выгрузке.")
            QMessageBox.warning(self, "Ошибка выгрузки", f"Произошла ошибка:\n{error_msg}")
            return

        field_links: Dict[str, str] = summary.get("field_links", {})
        if self.auto_bind_chk.isChecked() and field_links:
            for f in self.tab.fields:
                if f.id in field_links:
                    f.cloud_link = field_links[f.id]
            self.links_updated = True

        if self._last_report_folder and self._last_report_folder.get("webViewLink"):
            self.open_folder_btn.show()

        uploaded = summary.get("uploaded", 0)
        skipped = summary.get("skipped", 0)
        deleted = summary.get("deleted", 0)
        folder_name = (self._last_report_folder or {}).get("name", "")

        details = (
            f"Папка: {folder_name}\n"
            f"Загружено новых файлов: {uploaded}\n"
            f"Пропущено (уже в облаке): {skipped}\n"
            f"Удалено из облака: {deleted}"
        )
        if self.auto_bind_chk.isChecked():
            details += "\n\nСсылки на подпапки автоматически привязаны к полям отчёта."

        QMessageBox.information(self, "Выгрузка завершена", details)

    def open_last_folder_in_browser(self):
        if self._last_report_folder and self._last_report_folder.get("webViewLink"):
            QDesktopServices.openUrl(QUrl(self._last_report_folder["webViewLink"]))
