"""User Guide and Manual Dialog for EMS Reporter."""

from __future__ import annotations

from typing import Dict
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QTextBrowser,
    QPushButton,
    QLabel,
    QFrame,
)

HELP_ARTICLES: Dict[str, str] = {
    "intro": """
<h2>📖 Руководство пользователя EMS Reporter</h2>
<p><b>EMS Reporter</b> — специализированная программа для сотрудников фракции <b>Emergency Medical Services (EMS)</b> на проекте <b>Majestic GTA V RP</b>. Она разработана для автоматического подсчёта выполненных действий и баллов, избавляя вас от необходимости вручную пересчитывать сотни скриншотов и сообщений перед сдачей отчёта.</p>

<h3>⚡ Быстрый старт:</h3>
<ol>
  <li>В шапке программы введите ваше <b>Имя Фамилия</b> и <b>Статик #ID</b>.</li>
  <li>Нажмите <b>«➕ Добавить вкладку»</b> и создайте нужную вкладку (например, <i>Paramedic</i> или <i>DI</i>).</li>
  <li>В созданной вкладке нажмите <b>«➕ Добавить поле»</b> и настройте нужное действие:
    <ul>
      <li>Укажите папку со скриншотами для автоподсчёта;</li>
      <li>Или выберите числовое поле для ручных нормативов;</li>
      <li>Или вставьте ссылки на сообщения в Discord.</li>
    </ul>
  </li>
  <li>В конце рабочего дня или недели нажмите <b>«📝 Сформировать отчёт»</b> — программа сгенерирует чистые поля со всеми подсчитанными баллами, готовые для копирования в Google-форму или канал отчётов фракции!</li>
</ol>
""",

    "tabs_management": """
<h2>📑 Управление вкладками</h2>
<p>Вкладки служат для разделения отчётности (например, по отделам фракции, дням недели или направлениям работы).</p>

<h3>Основные действия:</h3>
<ul>
  <li><b>Создание вкладки:</b> На панели инструментов нажмите кнопку <b>«➕ Добавить вкладку»</b>. Введите название и при желании короткое описание.</li>
  <li><b>Редактирование:</b> Внутри нужной вкладки нажмите кнопку <b>«⚙ Вкладка»</b>, чтобы изменить название или описание.</li>
  <li><b>Смена порядка:</b> Вы можете перетаскивать вкладки мышью влево и вправо прямо на панели вкладок.</li>
  <li><b>Удаление:</b> Нажмите <b>«🗑 Удалить вкладку»</b>, чтобы удалить вкладку со всеми настроенными в ней полями.</li>
</ul>

<div style="background-color: #0b1827; border-left: 3px solid #38bdf8; padding: 8px 12px; margin-top: 10px;">
  <b>💡 Общий итог:</b> Бейдж в правом верхнем углу рассчитывает баллы и выполненные действия <u>строго по текущей открытой вкладке</u>, мгновенно пересчитываясь при переключении.
</div>
""",

    "field_folder": """
<h2>📁 Тип поля: «Папка со скриншотами»</h2>
<p>Используется для действий, подтверждением которых являются скриншоты в папке на вашем компьютере (реанимации, выдача таблеток, вакцинация и т.д.).</p>

<h3>Как это работает:</h3>
<ul>
  <li>Вы указываете название поля, путь к локальной папке и стоимость одного скриншота в баллах.</li>
  <li>Программа автоматически считывает количество файлов изображений (<code>.png</code>, <code>.jpg</code>, <code>.jpeg</code>, <code>.webp</code>, <code>.bmp</code>) и рассчитывает итоговые баллы:
    <br><br>
    <code style="background-color: #07101b; padding: 4px 8px; border-radius: 4px; color: #38bdf8;">
    Баллы = Количество скриншотов × Баллы за 1 скриншот
    </code>
  </li>
  <li><b>Автообновление:</b> Когда вы делаете новые скриншоты во время игры и сохраняете их в папку, программа автоматически пересчитывает баллы в фоновом режиме.</li>
  <li><b>Кнопка «Открыть»:</b> Мгновенно открывает выбранную папку в Проводнике Windows для удобного просмотра файлов.</li>
</ul>
""",

    "field_batch": """
<h2>⚖️ Пакетный расчёт баллов (с отбрасыванием остатка)</h2>
<p>Специальная опция для папок со скриншотами, когда баллы начисляются не за каждый отдельный скриншот, а строго за определённую пачку/комплект скриншотов, а некратный остаток сгорает.</p>

<h3>Настройка:</h3>
<ol>
  <li>В настройках поля типа «Папка со скриншотами» включите галочку <b>«☑ Считать баллами за набор скриншотов (с отбрасыванием остатка)»</b>.</li>
  <li>Задайте размер пачки и количество баллов (например: <i>за каждые 4 скриншота давать 30 баллов</i>).</li>
</ol>

<h3>Пример расчёта:</h3>
<ul>
  <li>Если в папке <b>8 скриншотов</b>: <code>8 // 4 = 2 набора</code> &rarr; <b>60 баллов</b>.</li>
  <li>Если в папке <b>7 скриншотов</b>: <code>7 // 4 = 1 набор</code> &rarr; <b>30 баллов</b> (3 лишних скриншота отброшены).</li>
  <li>Если в папке <b>3 скриншота</b>: набора нет &rarr; <b>0 баллов</b> (в отчёте отобразится <code>-</code>).</li>
</ul>
""",

    "field_numeric": """
<h2>🔢 Тип поля: «Числовое поле (ручной ввод)»</h2>
<p>Используется для действий, которые не подтверждаются отдельными скриншотами или учитываются по счётчику (например, участие в мероприятии, счастливый вызов, выдача комплектов мед. справок).</p>

<h3>Особенности:</h3>
<ul>
  <li>В настройках задаётся название и количество баллов за единицу действия.</li>
  <li>На главном экране прямо на карточке поля расположен счётчик <b>[ N ]</b>, значение которого можно быстро менять стрелками или ввести с клавиатуры.</li>
  <li>Справа моментально отображается пересчёт баллов, например: <code>(2 шт - 10 б)</code>.</li>
</ul>
""",

    "field_simple_links": """
<h2>🔗 Тип поля: «Ссылки на сообщения (баллы за ссылку)»</h2>
<p>Классический способ учёта ссылок на сообщения в спец. связи Discord (проверки, аудиты, журналы дежурств), где <b>каждая ссылка равна одной выполненной единице</b>.</p>

<h3>Как пользоваться:</h3>
<ol>
  <li>Нажмите кнопку <b>«🔗 Ссылки (X)»</b> на карточке поля.</li>
  <li>Вставьте ссылки списком (по одной на строку) или нажмите <b>«📋 Вставить из буфера»</b>.</li>
  <li>Программа подсчитает количество непустых строк и умножит на заданный балл.</li>
</ol>

<h3>Отображение в отчёте:</h3>
<p>Ссылки выводятся одна под другой, а в конце указывается общий итог:</p>
<pre style="background-color: #07101b; padding: 10px; border-radius: 6px; color: #cbd5e1;">
https://discord.com/channels/.../1298371928374
https://discord.com/channels/.../1298371928375
(2 шт - 10 б)
</pre>
""",

    "field_links_tasks": """
<h2>💬 Тип поля: «Ссылки с подсчётом задач (баллы за задачи)»</h2>
<p>Продвинутый режим для спец. связи, когда в одном сообщении Discord может быть зафиксировано несколько выполненных действий (например, в одном посте прикреплено сразу 3 реанимации или 5 справок).</p>

<h3>Как пользоваться:</h3>
<ol>
  <li>Нажмите кнопку <b>«💬 Задачи (X)»</b> на карточке поля.</li>
  <li>Откроется редактор, где для каждой ссылки указывается точное количество задач в поле <b>«Задач: [ N ]»</b>.</li>
  <li>Для каждой отдельной строки сразу показывается её подитог: <code>(3 шт - 9 б)</code>.</li>
  <li>Можно быстро добавлять новые строки кнопкой <b>«➕ Добавить строку»</b> или вставить скопированный текст.</li>
</ol>

<h3>Отображение в отчёте:</h3>
<p>Каждая ссылка отображается со своим количеством задач и баллов, а внизу подводится суммарный итог:</p>
<pre style="background-color: #07101b; padding: 10px; border-radius: 6px; color: #cbd5e1;">
https://discord.com/channels/.../1567539641345773609 (3 шт - 9 б)
https://discord.com/channels/.../1567539349388656681 (2 шт - 6 б)
https://discord.com/channels/.../1567505934501023757 (5 шт - 15 б)
(10 шт - 30 б)
</pre>
""",

    "cloud_link": """
<h2>☁️ Ссылка на облачное хранилище (Google Drive, Imgur)</h2>
<p>Необязательный параметр, доступный для полей со скриншотами и числовым вводом.</p>

<ul>
  <li>Если вы загружаете скриншоты в общую папку на Google Диске или в альбом Imgur, вставьте ссылку на эту папку в настройках поля.</li>
  <li>На главном экране ссылка не загромождает карточку.</li>
  <li>При формировании отчёта ссылка автоматически подставится перед результатом:
    <br><br>
    <code>https://drive.google.com/drive/folders/... (10 шт - 20 б)</code>
  </li>
  <li>Если ссылка не указана, в отчёт попадёт только результат: <code>(10 шт - 20 б)</code>.</li>
</ul>
""",

    "report_generation": """
<h2>📝 Формирование и сдача отчёта</h2>
<p>По нажатию кнопки <b>«📝 Сформировать отчёт»</b> открывается специализированное окно, подготовленное для быстрого заполнения форм.</p>

<h3>Структура окна отчёта:</h3>
<ol>
  <li><b>Первое поле:</b> <code>Имя Фамилия | статик</code> (например: <i>Jason Mitsui | 206277</i>).</li>
  <li><b>Промежуточные поля:</b> Каждое действие из активной вкладки вынесено в отдельную строку. Если поле набрало 0 баллов, автоматически выводится прочерк <code>-</code>.</li>
  <li><b>Последнее поле:</b> <code>Общее количество баллов</code> (например: <i>58</i>).</li>
</ol>

<h3>Удобство сдачи:</h3>
<ul>
  <li><b>Индивидуальное копирование:</b> Напротив каждого поля есть кнопка <b>«📋 Скопировать»</b>. Нажали &rarr; перешли в Google-форму &rarr; нажали <code>Ctrl+V</code>.</li>
  <li><b>Скопировать весь отчёт:</b> Кнопка внизу копирует весь текст отчёта целиком.</li>
  <li><b>Сохранение в .txt:</b> Позволяет сохранить готовый отчёт в текстовый файл на диске.</li>
</ul>
""",

    "config_export": """
<h2>💾 Сохранение, экспорт и импорт настроек</h2>
<p>Все ваши настройки вкладок, путей к папкам, ссылок и баллов сохраняются автоматически в файл <code>ems_config.json</code>.</p>

<h3>Обмен между игроками:</h3>
<ul>
  <li><b>«📤 Экспорт»:</b> Позволяет сохранить текущую конфигурацию в отдельный файл (например, <code>Шаблон_EMS.json</code>) и отправить его коллегам или интернам.</li>
  <li><b>«📥 Импорт»:</b> Позволяет в один клик применить готовый файл настроек, полученный от руководства отдела или другого сотрудника.</li>
  <li><b>«↺ Сброс»:</b> Полностью очищает все вкладки и поля, возвращая приложение к чистому стартовому состоянию.</li>
</ul>
""",

    "build_exe": """
<h2>📦 Сборка программы в автономный .EXE для Windows</h2>
<p>Вы можете скомпилировать приложение в один независимый исполняемый файл <b>EMS_Reporter.exe</b>, который будет работать на любом компьютере с Windows без установки Python.</p>

<h3>Как собрать файл:</h3>
<ol>
  <li>На компьютере с Windows дважды кликните по файлу <b><code>build_exe.bat</code></b>.</li>
  <li>Скрипт автоматически подготовит окружение, упакует библиотеки, код и медицинскую иконку.</li>
  <li>По завершении откроется папка <b><code>dist</code></b> с готовым файлом <b><code>EMS_Reporter.exe</code></b>.</li>
  <li>Этот файл можно отправить коллегам в Discord или Telegram — он запускается сразу в один клик!</li>
</ol>
"""
}


class HelpDialog(QDialog):
    """User Manual dialog with a navigation tree on the left and rich articles on the right."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Руководство пользователя — EMS Reporter")
        self.resize(960, 640)
        self.setMinimumSize(740, 480)
        self.setup_ui()
        self.populate_tree()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 12, 14, 12)
        main_layout.setSpacing(10)

        # Header banner
        header = QFrame()
        header.setStyleSheet("background-color: #0f2234; border: 1px solid #1a3650; border-radius: 6px; padding: 8px 14px;")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title_lbl = QLabel("📖 Руководство пользователя • EMS Reporter")
        title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #38bdf8;")
        h_layout.addWidget(title_lbl)
        h_layout.addStretch()
        main_layout.addWidget(header)

        # Splitter with Tree and Content
        splitter = QSplitter(Qt.Horizontal)
        splitter.setStyleSheet("QSplitter::handle { background-color: #1a3650; width: 2px; }")

        # Left: Navigation Tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 6, 0)
        left_layout.setSpacing(6)

        tree_title = QLabel("Разделы руководства:")
        tree_title.setStyleSheet("font-weight: 700; color: #94a3b8; font-size: 11px;")
        left_layout.addWidget(tree_title)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setFixedWidth(260)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #07101b;
                border: 1px solid #1e3a57;
                border-radius: 6px;
                padding: 4px;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 5px 8px;
                border-radius: 4px;
                color: #cbd5e1;
            }
            QTreeWidget::item:hover {
                background-color: #12273e;
                color: #38bdf8;
            }
            QTreeWidget::item:selected {
                background-color: #0284c7;
                color: #ffffff;
                font-weight: 600;
            }
        """)
        self.tree.currentItemChanged.connect(self.on_topic_selected)
        left_layout.addWidget(self.tree)
        splitter.addWidget(left_widget)

        # Right: Content Viewer
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(6, 0, 0, 0)
        right_layout.setSpacing(6)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(True)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: #07101b;
                border: 1px solid #1e3a57;
                border-radius: 6px;
                padding: 16px 20px;
                color: #e2e8f0;
                font-size: 13px;
                line-height: 1.5;
            }
        """)
        right_layout.addWidget(self.browser)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 1)

        # Bottom Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Закрыть руководство")
        close_btn.setObjectName("secondaryButton")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        main_layout.addLayout(btn_layout)

    def populate_tree(self):
        """Build topics hierarchy in the left navigation tree."""
        # 1. Introduction
        item_intro = QTreeWidgetItem(["🚀 Введение и быстрый старт"])
        item_intro.setData(0, Qt.UserRole, "intro")
        self.tree.addTopLevelItem(item_intro)

        # 2. Tabs
        item_tabs = QTreeWidgetItem(["📑 Управление вкладками"])
        item_tabs.setData(0, Qt.UserRole, "tabs_management")
        self.tree.addTopLevelItem(item_tabs)

        # 3. Field Types (Category)
        item_fields_cat = QTreeWidgetItem(["📁 Типы отчётных полей"])
        item_fields_cat.setExpanded(True)

        f_folder = QTreeWidgetItem(["1. Папка со скриншотами"])
        f_folder.setData(0, Qt.UserRole, "field_folder")
        item_fields_cat.addChild(f_folder)

        f_batch = QTreeWidgetItem(["2. Пакетный расчёт скриншотов"])
        f_batch.setData(0, Qt.UserRole, "field_batch")
        item_fields_cat.addChild(f_batch)

        f_numeric = QTreeWidgetItem(["3. Числовое поле (ручной ввод)"])
        f_numeric.setData(0, Qt.UserRole, "field_numeric")
        item_fields_cat.addChild(f_numeric)

        f_slinks = QTreeWidgetItem(["4. Ссылки (баллы за ссылку)"])
        f_slinks.setData(0, Qt.UserRole, "field_simple_links")
        item_fields_cat.addChild(f_slinks)

        f_tlinks = QTreeWidgetItem(["5. Ссылки с задачами"])
        f_tlinks.setData(0, Qt.UserRole, "field_links_tasks")
        item_fields_cat.addChild(f_tlinks)

        f_cloud = QTreeWidgetItem(["6. Облачное хранилище"])
        f_cloud.setData(0, Qt.UserRole, "cloud_link")
        item_fields_cat.addChild(f_cloud)

        self.tree.addTopLevelItem(item_fields_cat)

        # 4. Report Generation
        item_rep = QTreeWidgetItem(["📝 Формирование отчёта"])
        item_rep.setData(0, Qt.UserRole, "report_generation")
        self.tree.addTopLevelItem(item_rep)

        # 5. Config Management
        item_cfg = QTreeWidgetItem(["💾 Экспорт и импорт настроек"])
        item_cfg.setData(0, Qt.UserRole, "config_export")
        self.tree.addTopLevelItem(item_cfg)

        # 6. Standalone Exe Build
        item_exe = QTreeWidgetItem(["📦 Сборка в автономный .EXE"])
        item_exe.setData(0, Qt.UserRole, "build_exe")
        self.tree.addTopLevelItem(item_exe)

        # Select first item by default
        self.tree.setCurrentItem(item_intro)

    def on_topic_selected(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        if not current:
            return
        topic_key = current.data(0, Qt.UserRole)
        if topic_key and topic_key in HELP_ARTICLES:
            self.browser.setHtml(HELP_ARTICLES[topic_key])
        elif current.childCount() > 0:
            # If clicked on category header, show first child
            first_child = current.child(0)
            topic_key = first_child.data(0, Qt.UserRole)
            if topic_key in HELP_ARTICLES:
                self.browser.setHtml(HELP_ARTICLES[topic_key])
