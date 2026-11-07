"""About Dialog for EMS Reporter."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)


from app import __version__


class AboutDialog(QDialog):
    """Dialog displaying application information, purpose, and GitHub link."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе — EMS Reporter")
        self.setFixedSize(540, 460)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Main Card with objectName so style does not cascade to children
        card = QFrame()
        card.setObjectName("aboutCard")
        card.setStyleSheet("""
            #aboutCard {
                background-color: #0f2234;
                border: 1px solid #1a3650;
                border-radius: 8px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(18, 18, 18, 18)
        card_layout.setSpacing(12)

        # Header row: Icon + App Title
        h_row = QHBoxLayout()
        h_row.setSpacing(12)

        icon_lbl = QLabel()
        base_dir = Path(__file__).resolve().parent.parent
        for icon_name in ["icon.png", "icon.ico"]:
            icon_file = base_dir / icon_name
            if icon_file.is_file():
                pix = QPixmap(str(icon_file)).scaled(54, 54, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                icon_lbl.setPixmap(pix)
                break
        else:
            icon_lbl.setText("🚑")
            icon_lbl.setStyleSheet("font-size: 38px;")

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        app_title = QLabel("EMS Reporter")
        app_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #38bdf8;")
        app_sub = QLabel("Majestic GTA V RP • Emergency Medical Services")
        app_sub.setStyleSheet("font-size: 11px; color: #94a3b8;")
        version_lbl = QLabel(f"Версия {__version__} • 2026")
        version_lbl.setStyleSheet("font-size: 11px; color: #10b981; font-weight: 600;")

        title_box.addWidget(app_title)
        title_box.addWidget(app_sub)
        title_box.addWidget(version_lbl)

        h_row.addWidget(icon_lbl)
        h_row.addLayout(title_box, 1)
        card_layout.addLayout(h_row)

        # Description
        desc_lbl = QLabel(
            "Программа для автоматизации еженедельных и ежедневных отчётов сотрудников фракции EMS:\n\n"
            "• Автоматический подсчёт файлов скриншотов в папках с поддержкой пакетного начисления баллов;\n"
            "• Подсчёт ссылок на сообщения в Discord (поштучно и с указанием выполненных задач);\n"
            "• Ручной учёт нормативов;\n"
            "• Формирование чистого отчёта для мгновенной сдачи в Google-формы и на форум."
        )
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #cbd5e1; line-height: 1.4;")
        card_layout.addWidget(desc_lbl)

        # GitHub Repo & Releases Links
        links_box = QVBoxLayout()
        links_box.setSpacing(6)

        repo_lbl = QLabel("Официальный репозиторий GitHub:")
        repo_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        github_link = QLabel(
            '<a href="https://github.com/Zefous/EMS-Reporter" style="color: #38bdf8; text-decoration: underline; font-weight: bold;">'
            'https://github.com/Zefous/EMS-Reporter</a>'
        )
        github_link.setOpenExternalLinks(True)
        github_link.setTextInteractionFlags(Qt.TextBrowserInteraction)

        releases_lbl = QLabel("Страница релизов (готовые версии программы):")
        releases_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #94a3b8;")
        releases_link = QLabel(
            '<a href="https://github.com/Zefous/EMS-Reporter/releases" style="color: #38bdf8; text-decoration: underline; font-weight: bold;">'
            'https://github.com/Zefous/EMS-Reporter/releases</a>'
        )
        releases_link.setOpenExternalLinks(True)
        releases_link.setTextInteractionFlags(Qt.TextBrowserInteraction)

        links_box.addWidget(repo_lbl)
        links_box.addWidget(github_link)
        links_box.addWidget(releases_lbl)
        links_box.addWidget(releases_link)
        card_layout.addLayout(links_box)

        layout.addWidget(card, 1)

        # Bottom close button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Закрыть")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedWidth(110)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
