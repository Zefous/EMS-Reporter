"""Update Dialog for downloading and installing new versions."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextBrowser,
    QMessageBox,
    QFrame,
)

from app import __version__
from app.updater import ReleaseInfo, DownloadUpdateThread, apply_update_and_restart


class UpdateDialog(QDialog):
    """Dialog showing release notes, download progress, and in-place restart."""

    def __init__(self, release: ReleaseInfo, parent=None):
        super().__init__(parent)
        self.release = release
        self.download_thread: Optional[DownloadUpdateThread] = None
        self.downloaded_file: Optional[str] = None

        self.setWindowTitle("Обновление — EMS Reporter")
        self.resize(620, 500)
        self.setMinimumSize(500, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        # Header banner
        header = QFrame()
        header.setStyleSheet("background-color: #0f2234; border: 1px solid #1a3650; border-radius: 8px; padding: 12px 16px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        title = QLabel(f"🚀 Доступна новая версия: {self.release.tag_name}")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")

        ver_sub = QLabel(f"Текущая версия: <b>v{__version__}</b>  →  Новая версия: <b>{self.release.tag_name}</b>")
        ver_sub.setStyleSheet("font-size: 12px; color: #38bdf8;")

        h_layout.addWidget(title)
        h_layout.addWidget(ver_sub)
        layout.addWidget(header)

        # Release description title
        lbl_notes = QLabel("Что нового в этом обновлении:")
        lbl_notes.setStyleSheet("font-weight: 700; color: #cbd5e1; font-size: 12px;")
        layout.addWidget(lbl_notes)

        # Changelog browser
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        # Format markdown/plaintext as HTML
        body_html = self.release.body.replace("\n", "<br>")
        self.browser.setHtml(f"<div style='font-family: sans-serif; font-size: 12px; color: #e2e8f0; line-height: 1.4;'>{body_html}</div>")
        self.browser.setStyleSheet("background-color: #07101b; border: 1px solid #1e3a57; border-radius: 6px; padding: 10px;")
        layout.addWidget(self.browser, 1)

        # Progress bar container (hidden until download starts)
        self.progress_container = QFrame()
        p_layout = QVBoxLayout(self.progress_container)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.setSpacing(4)

        self.progress_lbl = QLabel("Подготовка к скачиванию...")
        self.progress_lbl.setStyleSheet("font-size: 11px; color: #94a3b8;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #07101b;
                border: 1px solid #1e3a57;
                border-radius: 4px;
                text-align: center;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #0284c7;
                border-radius: 3px;
            }
        """)

        p_layout.addWidget(self.progress_lbl)
        p_layout.addWidget(self.progress_bar)
        layout.addWidget(self.progress_container)
        self.progress_container.hide()

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.github_btn = QPushButton("🌐 Открыть на GitHub")
        self.github_btn.setObjectName("secondaryButton")
        self.github_btn.clicked.connect(self.open_github_release)

        self.cancel_btn = QPushButton("Позже")
        self.cancel_btn.setObjectName("secondaryButton")
        self.cancel_btn.clicked.connect(self.reject)

        self.action_btn = QPushButton("⬇ Загрузить и обновить")
        self.action_btn.setObjectName("primaryButton")
        self.action_btn.setDefault(True)
        self.action_btn.clicked.connect(self.start_download)

        btn_layout.addWidget(self.github_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.action_btn)
        layout.addLayout(btn_layout)

    def open_github_release(self):
        url = QUrl(self.release.html_url)
        QDesktopServices.openUrl(url)

    def start_download(self):
        if not self.release.download_url:
            QMessageBox.information(
                self,
                "Обновление",
                "Исполняемый файл ещё не прикреплен к этому релизу на GitHub.\n"
                "Вы можете перейти на страницу релизов и скачать его вручную."
            )
            self.open_github_release()
            return

        # Determine download target location next to executable or cwd
        if getattr(sys, "frozen", False):
            base_dir = Path(sys.executable).resolve().parent
        else:
            base_dir = Path.cwd()

        update_dest = base_dir / "EMS_Reporter.update"

        self.action_btn.setEnabled(False)
        self.action_btn.setText("⏳ Загрузка...")
        self.cancel_btn.setEnabled(False)
        self.progress_container.show()

        self.download_thread = DownloadUpdateThread(self.release.download_url, update_dest, self)
        self.download_thread.progress.connect(self.on_download_progress)
        self.download_thread.finished_download.connect(self.on_download_finished)
        self.download_thread.failed.connect(self.on_download_failed)
        self.download_thread.start()

    def on_download_progress(self, percent: int, downloaded: int, total: int):
        self.progress_bar.setValue(percent)
        dl_mb = downloaded / (1024 * 1024)
        if total > 0:
            tot_mb = total / (1024 * 1024)
            self.progress_lbl.setText(f"Загрузка: {percent}% ({dl_mb:.1f} МБ из {tot_mb:.1f} МБ)")
        else:
            self.progress_lbl.setText(f"Загрузка: {dl_mb:.1f} МБ...")

    def on_download_finished(self, file_path: str):
        self.downloaded_file = file_path
        self.progress_bar.setValue(100)
        self.progress_lbl.setText("✓ Загрузка успешно завершена!")
        self.progress_lbl.setStyleSheet("font-size: 11px; color: #10b981; font-weight: bold;")

        self.action_btn.setEnabled(True)
        self.action_btn.setText("🔄 Перезапустить и применить")
        self.action_btn.setStyleSheet("background-color: #059669; color: white;")
        self.action_btn.clicked.disconnect()
        self.action_btn.clicked.connect(self.restart_and_apply)

        self.cancel_btn.setEnabled(True)
        self.cancel_btn.setText("Закрыть")

    def on_download_failed(self, error: str):
        self.progress_container.hide()
        self.action_btn.setEnabled(True)
        self.action_btn.setText("⬇ Попробовать снова")
        self.cancel_btn.setEnabled(True)
        QMessageBox.warning(self, "Ошибка загрузки", f"Не удалось загрузить файл обновления:\n{error}")

    def restart_and_apply(self):
        if not self.downloaded_file:
            return

        success = apply_update_and_restart(self.downloaded_file)
        if success:
            self.accept()
            QApplication.quit()
            sys.exit(0)
        else:
            QMessageBox.information(
                self,
                "Обновление загружено",
                f"Файл обновления успешно скачан:\n{self.downloaded_file}\n\n"
                "Поскольку программа запущена из исходного кода Python, автоматический перезапуск в .exe не требуется."
            )
            self.accept()
