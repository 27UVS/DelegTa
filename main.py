import os
import re
import sys
import json
import uuid

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QDialog, QTextEdit, QDateTimeEdit, QInputDialog,
    QFileDialog, QFrame, QLineEdit, QMessageBox, QScrollArea, QColorDialog, QComboBox, QSizePolicy, QCheckBox, QTextBrowser
)
from PySide6.QtGui import QPixmap, QIcon, QColor, QDesktopServices, QDrag
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QSettings, QSize, QEasingCurve, QUrl, QDateTime, QMimeData

base_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DelegTa")
        self.setWindowIcon(QIcon(os.path.join(base_dir, "db/images/interface/icon.png")))
        self.json_path = os.path.join(os.path.dirname(__file__), "db/members.json")

        # --- Загружаем сохранённый фон ---
        self.settings = QSettings("27UVS", "DelegTaApp")
        saved_path = self.settings.value("background_path", os.path.join(base_dir, "background.jpg"))
        if not isinstance(saved_path, str):
            saved_path = str(saved_path)
        self.bg_path = saved_path if os.path.exists(saved_path) else os.path.join(base_dir, "background.jpg")

        # --- Фон ---
        self.bg_label = QLabel(self)
        self.bg_label.setScaledContents(True)
        self.bg_pixmap = QPixmap(self.bg_path)
        self.bg_label.setPixmap(self.bg_pixmap)

        # --- Кнопка настроек ---
        self.btn_active = QIcon(os.path.join(base_dir, "db/images/interface/settings_active.png"))
        self.btn_default = QIcon(os.path.join(base_dir, "db/images/interface/settings_default.png"))

        self.settings_btn = HoverButton(self.btn_default, self.btn_active, self)
        self.settings_btn.clicked.connect(self.toggle_settings_panel)
        # self.settings_btn.raise_()

        # --- Основной контент ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Основная область с панелями ---
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)

        # --- Панель участников с кнопкой их добавления ---
        self.members_panel = QFrame()
        self.members_panel.setFixedWidth(312)
        self.members_panel.setStyleSheet("""
            background-color: rgb(30, 30, 30);
            border: none;
            color: white;
        """)

        members_layout = QVBoxLayout()
        members_layout.setContentsMargins(15, 15, 15, 15)

        # --- Заголовок панели участников ---
        header_layout = QHBoxLayout()
        title_label = QLabel("Участники")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)

        # Кнопка добавления участника
        btn_add = os.path.join(base_dir, "db/images/interface/add.png")
        self.add_member_overlay = AddMemberOverlay(self, parent=self, json_path=os.path.join(base_dir,
                                                                                             "db/members.json"))
        self.add_member_btn = QPushButton()
        self.add_member_btn.setIcon(QIcon(btn_add))
        self.add_member_btn.setIconSize(QSize(30, 30))
        self.add_member_btn.setFixedSize(40, 40)
        self.add_member_btn.setStyleSheet("""
            background-color: #444;
            border-radius: 20px;
            border: none;
        """)
        self.add_member_btn.clicked.connect(self.add_member_overlay.show_overlay)
        header_layout.addStretch()
        header_layout.addWidget(self.add_member_btn)

        members_layout.addLayout(header_layout)

        # Область прокрутки участников
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        # Контейнер для блоков участников
        self.members_container = QWidget()
        self.members_container_layout = QVBoxLayout(self.members_container)
        self.members_container_layout.setContentsMargins(0, 0, 0, 0)
        self.members_container_layout.setSpacing(8)
        self.members_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.scroll_area.setWidget(self.members_container)
        members_layout.addWidget(self.scroll_area)

        # Панель редактирования должностей
        self.members_panel.setLayout(members_layout)
        self.update_members_tasks_count()
        self.refresh_members_list()
        content_layout.addWidget(self.members_panel)

        # Правая часть с задачами
        tasks_container = QVBoxLayout()
        tasks_container.setContentsMargins(5, 40, 5, 5)

        # --- 4 панели ---
        tasks_row = QHBoxLayout()
        tasks_row.setSpacing(15)

        # Панели задач
        self.columns = []
        self.scroll_areas = []

        colors = {
            "Черновик": "rgba(62, 95, 138, 220)",
            "В процессе": "rgba(229, 81, 55, 220)",
            "Завершено": "rgba(154, 205, 50, 220)",
            "Отложено": "rgba(102, 0, 102, 220)"
        }
        titles = ["Черновик", "В процессе", "Завершено", "Отложено"]

        for title in titles:
            outer_frame = QFrame()
            outer_frame.setStyleSheet(f"""
                background-color: {colors[title]};
                border-radius: 20px;
                border: 1px solid #ccc;
            """)
            outer_layout = QVBoxLayout(outer_frame)
            outer_layout.setContentsMargins(10, 10, 10, 10)

            # Заголовок
            header_layout = QHBoxLayout()
            header_label = QLabel(title)
            header_label.setStyleSheet("color: #333; font-size: 18px; font-weight: bold;")
            header_layout.addWidget(header_label)
            header_layout.addStretch()

            # Кнопка добавления задачи только для "Черновик"
            if title == "Черновик":
                add_task_btn = QPushButton()
                add_task_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/add.png")))
                add_task_btn.setIconSize(QSize(32, 32))
                add_task_btn.setFixedSize(30, 30)
                add_task_btn.setStyleSheet("""
                    background-color: #4CAF50;
                    color: white;
                    font-size: 18px;
                    font-weight: bold;
                    border: none;
                    border-radius: 14px;
                """)
                add_task_btn.clicked.connect(self.show_add_task_overlay)
                header_layout.addWidget(add_task_btn)

            header_frame = QFrame()
            header_frame.setLayout(header_layout)
            header_frame.setStyleSheet("background-color: white; border-radius: 10px;")
            outer_layout.addWidget(header_frame)

            # QScrollArea для задач
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setStyleSheet("background: transparent; border: none;")
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

            # Внутренний TaskPanel (поддерживает drag & drop)
            task_panel = TaskPanel(status=title, main_window=self, on_edit_callback=self.open_edit_task)
            container_widget = QWidget()
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(5, 5, 5, 5)
            container_layout.setSpacing(10)
            container_layout.addWidget(task_panel)
            scroll_area.setWidget(container_widget)

            outer_layout.addWidget(scroll_area)
            tasks_row.addWidget(outer_frame)

            # Сохраняем
            self.columns.append(task_panel)
            self.scroll_areas.append(scroll_area)

        # Загружаем задачи
        self.load_tasks_into_panels()

        tasks_container.addLayout(tasks_row)
        content_layout.addLayout(tasks_container)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # --- Панель настроек ---
        self.edit_positions_overlay = EditPositionsOverlay(parent=self, main_window=self)
        self.settings_panel = SettingsPanel(
            self,
            on_close=self.toggle_settings_panel,
            on_change_background=self.change_background,
            on_edit_positions=EditPositionsOverlay(parent=self, main_window=self).show_overlay
        )
        self.settings_panel.setGeometry(self.width(), 0, 300, self.height())
        self.panel_visible = False

    def init_members_panel(self):
        """Создаем панель участников с прокруткой"""
        self.members_panel = QFrame()
        self.members_panel.setFixedWidth(280)
        self.members_panel.setStyleSheet("""
            background-color: rgba(30, 30, 30, 230);
            border: none;
            color: white;
        """)

        members_layout = QVBoxLayout()
        members_layout.setContentsMargins(0, 0, 0, 0)
        members_layout.setSpacing(10)

        # Заголовок
        title_bar = QHBoxLayout()
        title = QLabel("Участники")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        title_bar.addWidget(title)
        title_bar.addStretch()
        members_layout.addLayout(title_bar)

        # Область прокрутки
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        # Контейнер для блоков участников
        self.members_container = QWidget()
        self.members_container_layout = QVBoxLayout(self.members_container)
        self.members_container_layout.setContentsMargins(0, 0, 0, 0)
        self.members_container_layout.setSpacing(8)

        self.scroll_area.setWidget(self.members_container)
        members_layout.addWidget(self.scroll_area)

    def refresh_members_list(self):
        # Очистить старые элементы
        for i in reversed(range(self.members_container_layout.count())):
            widget = self.members_container_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        json_path = os.path.join(os.path.dirname(__file__), "db/members.json")
        if not os.path.exists(json_path):
            return

        with open(json_path, "r", encoding="utf-8") as f:
            members = json.load(f)

        members = self.sort_members_by_post(members)

        for member in members:
            block = self.create_member_block(member)
            self.members_container_layout.addWidget(block)
        # self.members_container_layout.addStretch()

    @staticmethod
    def sort_members_by_post(members):
        post_priority = ["Руководитель", "Сценарист", "Художник", "Партнёр"]

        def get_priority(member):
            post = member.get("post", "")
            if post in post_priority:
                return post_priority.index(post)
            return len(post_priority)  # если должность не в списке, отправляем в конец

        return sorted(members, key=get_priority)

    def create_member_block(self, member):
        block = QFrame()
        block.setStyleSheet("""
            background-color: #2a2a2a;
            border-radius: 10px;
            padding: 8px;
        """)
        block.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        layout = QHBoxLayout(block)
        layout.setContentsMargins(0, 0, 10, 0)

        # --- Аватар ---
        avatar_label = QLabel()
        avatar_label.setFixedSize(60, 60)
        if member.get("avatar") and os.path.exists(member["avatar"]):
            pixmap = QPixmap(member["avatar"]).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)
            avatar_label.setPixmap(pixmap)
        else:
            avatar_label.setStyleSheet("background-color: #444; border-radius: 25px;")
        layout.addWidget(avatar_label)

        # --- Имя + должность ---
        info_container = QWidget()
        info_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)

        def insert_zero_width_spaces(text, max_chunk=10):
            import re
            # Разбиваем длинные слова длиннее max_chunk символов на части с \u200B
            def repl(match):
                word = match.group(0)
                parts = [word[i:i + max_chunk] for i in range(0, len(word), max_chunk)]
                return "\u200B".join(parts)

            return re.sub(r'\S{' + str(max_chunk + 1) + ',}', repl, text)

        # Имя
        name_label = QLabel(member.get("name", "Без имени"))
        name_label.setStyleSheet("font-weight: bold; color: white; font-size: 16px;")
        name_text = member.get("name", "Без имени")
        name_text_wrapped = insert_zero_width_spaces(name_text, max_chunk=9)
        name_label.setText(name_text_wrapped)
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        name_label.setMaximumWidth(110)
        name_label.setWordWrap(True)
        info_layout.addWidget(name_label)

        # Должность
        post = member.get("post")
        if post:
            post_color = self.get_post_color(post)
            short_post = post[:3].upper()
            post_label = QLabel(short_post)
            post_label.setStyleSheet(f"color: {post_color}; font-size: 14px;")
            info_layout.addWidget(post_label)
        else:
            info_layout.addWidget(QLabel(""))  # пустая строка
        layout.addWidget(info_container)

        # --- Число дел ---
        tasks_count = member.get("tasks", 0)  # если нет - 0
        tasks_label = QLabel(str(tasks_count))
        tasks_label.setFixedSize(40, 30)
        tasks_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tasks_label.setStyleSheet("""
            background-color: #555;
            color: white;
            border-radius: 15px;
            font-weight: bold;
            font-size: 16px;
        """)
        layout.addStretch()
        layout.addWidget(tasks_label)

        # --- Статус ---
        status_color = "#808080"  # серый
        if member.get("status") == "Доступен":
            status_color = "#00cc44"
        elif member.get("status") == "Занят":
            status_color = "#cc0000"

        status_indicator = QLabel()
        status_indicator.setFixedSize(16, 16)
        status_indicator.setStyleSheet(f"""
            background-color: {status_color};
            border-radius: 8px;
        """)
        layout.addWidget(status_indicator)

        block.mousePressEvent = lambda event, m=member: self.show_member_info(m)

        return block

    def show_add_task_overlay(self):
        self.task_overlay = AddTaskOverlay(parent=self, main_window=self, base_dir=base_dir)

    def load_tasks_into_panels(self):
        files_map = {
            "Черновик": os.path.join(base_dir, "db/tasks/draft_tasks.json"),
            "В процессе": os.path.join(base_dir, "db/tasks/progress_tasks.json"),
            "Завершено": os.path.join(base_dir, "db/tasks/finished_tasks.json"),
            "Отложено": os.path.join(base_dir, "db/tasks/delayed_tasks.json"),
        }

        for panel in self.columns:
            layout = panel.layout
            # Удаляем старые карточки (кроме Stretch)
            for i in reversed(range(layout.count() - 1)):
                item = layout.itemAt(i)
                if item.widget():
                    item.widget().deleteLater()

            # Загружаем задачи для конкретного статуса
            file_path = files_map[panel.status]
            if not os.path.exists(file_path):
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)

            for task in reversed(tasks):  # в обратном порядке
                panel.add_task(task)

    def add_task_card(self, layout, task):
        card = QFrame()
        card.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
        """)
        card.setFixedWidth(220)
        card.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Maximum)

        vbox = QVBoxLayout(card)
        vbox.setContentsMargins(8, 8, 8, 8)
        vbox.setSpacing(5)

        # 1. Название задачи
        name_label = QLabel(task.get("name", "Без названия"))
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: black;")
        vbox.addWidget(name_label)

        # 2. Ответственный
        responsible_id = task.get("responsible", "")
        responsible = self.get_member_by_id(responsible_id)
        responsible_name = responsible.get("name", "Неизвестный")
        resp_label = QLabel(f"Ответственный: {responsible_name}")
        resp_label.setWordWrap(True)
        resp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        resp_label.setStyleSheet("font-size: 14px; color: #333;")
        vbox.addWidget(resp_label)

        # 3. Время (зависит от условий)
        time_label = QLabel()
        if task.get("is_permanent"):
            time_label.setText("П")
            time_label.setStyleSheet("font-size: 14px; color: blue; font-weight: bold;")
        elif task.get("no_deadline"):
            created_date = QDateTime.fromString(task.get("created_at"), "dd.MM.yyyy HH:mm")
            if created_date.isValid():
                days = created_date.daysTo(QDateTime.currentDateTime())
                time_label.setText(f"{days} д.")
                time_label.setStyleSheet("font-size: 14px; color: gray;")
            else:
                time_label.setText("—")
        else:
            deadline = QDateTime.fromString(task.get("deadline"), "dd.MM.yyyy HH:mm")
            now = QDateTime.currentDateTime()
            if deadline.isValid():
                days_diff = now.daysTo(deadline)
                if days_diff >= 0:
                    time_label.setText(f"ост. {days_diff} д.")
                    time_label.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")
                else:
                    time_label.setText(f"проср. {abs(days_diff)} д.")
                    time_label.setStyleSheet("font-size: 14px; color: red; font-weight: bold;")
            else:
                time_label.setText("—")
        vbox.addWidget(time_label)

        layout.insertWidget(layout.count() - 1, card)  # вставляем перед stretch

    @staticmethod
    def get_member_by_id(member_id):
        members_path = os.path.join(base_dir, "db/members.json")
        if os.path.exists(members_path):
            with open(members_path, "r", encoding="utf-8") as f:
                members = json.load(f)
                for m in members:
                    if m.get("id") == member_id:
                        return m
        return "Неизвестно"

    @staticmethod
    def get_post_color(post_name):
        positions_path = os.path.join(base_dir, "db/positions.json")
        if os.path.exists(positions_path):
            with open(positions_path, "r", encoding="utf-8") as f:
                positions = json.load(f).get("positions", [])
                for pos in positions:
                    if pos["name"] == post_name:
                        return pos.get("color", "#FFFFFF")
        return "#FFFFFF"

    def refresh_positions_everywhere(self):
        """
        Обновляет:
        1. Цвет должностей в блоках участников.
        2. ComboBox должностей в окнах добавления/редактирования участника.
        """
        # 1. Обновляем список участников (цвет должностей пересчитается через get_post_color)
        self.refresh_members_list()

        # 2. Обновляем ComboBox в открытых окнах AddMemberOverlay или EditMemberOverlay
        # Проверяем все дочерние окна MainWindow
        for child in self.findChildren(QWidget):
            if hasattr(child, "load_positions"):  # Окно поддерживает загрузку должностей
                child.load_positions()

    @staticmethod
    def update_members_tasks_count():
        members_path = os.path.join(base_dir, "db/members.json")
        if not os.path.exists(members_path):
            return

        # Загружаем участников
        with open(members_path, "r", encoding="utf-8") as f:
            members = json.load(f)

        # Загружаем задачи из progress и delayed
        task_files = [
            os.path.join(base_dir, "db/tasks/progress_tasks.json"),
            os.path.join(base_dir, "db/tasks/delayed_tasks.json")
        ]

        task_counts = {}
        for file_path in task_files:
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                    for task in tasks:
                        responsible_id = task.get("responsible")
                        if responsible_id:
                            task_counts[responsible_id] = task_counts.get(responsible_id, 0) + 1

        # Обновляем количество задач у участников
        for member in members:
            member_id = member.get("id")
            member["tasks"] = task_counts.get(member_id, 0)

        # Сохраняем обновленный список
        with open(members_path, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=4)

    def move_task_to_panel(self, task_data, new_status):
        # Определяем, из какого JSON удалить, в какой добавить
        files_map = {
            "Черновик": "draft_tasks.json",
            "В процессе": "progress_tasks.json",
            "Завершено": "finished_tasks.json",
            "Отложено": "delayed_tasks.json"
        }

        # Удаляем из всех файлов
        for fname in files_map.values():
            path = os.path.join(base_dir, "db/tasks", fname)
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                tasks = [t for t in tasks if t.get("id") != task_data["id"]]
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=4)

        # Добавляем в новый файл
        new_file = os.path.join(base_dir, "db/tasks", files_map[new_status])
        if os.path.exists(new_file):
            with open(new_file, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        else:
            tasks = []
        tasks.append(task_data)
        with open(new_file, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

        self.load_tasks_into_panels()

        self.update_members_tasks_count()
        if hasattr(self, "refresh_members_list"):
            self.refresh_members_list()

    def toggle_settings_panel(self):
        """Анимация выезда панели"""
        start = self.settings_panel.geometry()
        if self.panel_visible:
            end = QRect(self.width(), 0, 300, self.height())
            self.settings_btn.setIcon(self.btn_default)  # возвращаем обычную иконку
        else:
            end = QRect(self.width() - 300, 0, 300, self.height())
            self.settings_btn.setIcon(self.btn_active)  # ставим активную иконку

        self.anim = QPropertyAnimation(self.settings_panel, b"geometry")
        self.anim.setDuration(300)
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()
        self.panel_visible = not self.panel_visible

    def change_background(self):
        """Выбор нового фона"""
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите фон", "", "Изображения (*.png *.jpg *.jpeg)")
        if file_name:
            self.bg_pixmap = QPixmap(file_name)
            self.bg_label.setPixmap(self.bg_pixmap)
            self.bg_path = file_name
            self.settings.setValue("background_path", file_name)
            self.resizeEvent(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)

        # Обновляем фон
        if hasattr(self, "bg_label"):
            self.bg_label.setGeometry(0, 0, self.width(), self.height())
            scaled = self.bg_pixmap.scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                           Qt.TransformationMode.SmoothTransformation)
            self.bg_label.setPixmap(scaled)

        # Обновляем панель настроек
        self.settings_panel.setGeometry(self.width() - (300 if self.panel_visible else 0), 0, 300, self.height())

        # Перемещаем кнопку в правый верхний угол
        self.settings_btn.move(self.width() - self.settings_btn.width() - 20, 5)

    def show_member_info(self, member):
        dialog = MemberInfoDialog(self, member, on_edit_callback=self.open_edit_member)
        dialog.exec()

    def open_edit_member(self, member):
        # Используем AddMemberOverlay, но в режиме редактирования
        self.add_member_overlay.edit_mode = True
        self.add_member_overlay.editing_member_id = member["id"]
        self.add_member_overlay.load_member(member)
        self.add_member_overlay.show_overlay()

    def open_edit_task(self, task_data, status):
        self.add_task_overlay = AddTaskOverlay(parent=self, main_window=self, base_dir=base_dir, task_data=task_data, status=status)
        self.add_task_overlay.show()


class TaskCard(QFrame):
    def __init__(self, task_data, main_window=None, panel_title=None, on_edit_callback=None):
        super().__init__()
        self.task_data = task_data
        self.main_window = main_window
        self.panel_title = panel_title
        self.on_edit_callback = on_edit_callback
        self.setStyleSheet("""
            background-color: white;
            border-radius: 10px;
            padding: 5px;
        """)
        self.setFixedWidth(170)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 8, 8, 8)

        # --- Название задания ---
        name_label = QLabel(task_data.get("name", "Без названия"))
        name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: black;")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        name_label.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        vbox.addWidget(name_label)

        # --- Ответственный за задание ---
        responsible_id = task_data.get("responsible", "")
        resp = main_window.get_member_by_id(responsible_id)
        resp_name = resp.get("name", "Неизвестный")
        resp_label = QLabel(f"Ответственный: {resp_name}")
        resp_label.setStyleSheet("font-size: 16px; color: #333;;")
        resp_label.setWordWrap(True)
        resp_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        vbox.addWidget(resp_label)

        # --- Время задания ---
        if self.panel_title != "Завершено":
            time_label = QLabel()
            if self.task_data.get("is_permanent"):
                time_label.setText("П")
                time_label.setStyleSheet("font-size: 14px; color: blue; font-weight: bold;")
            elif self.task_data.get("no_deadline"):
                created_date = QDateTime.fromString(self.task_data.get("created_at"), "dd.MM.yyyy HH:mm")
                if created_date.isValid():
                    days = created_date.daysTo(QDateTime.currentDateTime())
                    time_label.setText(f"{days} д.")
                    time_label.setStyleSheet("font-size: 14px; color: gray;")
                else:
                    time_label.setText("—")
            else:
                deadline = QDateTime.fromString(self.task_data.get("deadline"), "dd.MM.yyyy HH:mm")
                now = QDateTime.currentDateTime()
                if deadline.isValid():
                    days_diff = now.daysTo(deadline)
                    if days_diff >= 0:
                        time_label.setText(f"ост. {days_diff} д.")
                        time_label.setStyleSheet("font-size: 14px; color: green; font-weight: bold;")
                    else:
                        time_label.setText(f"проср. {abs(days_diff)} д.")
                        time_label.setStyleSheet("font-size: 14px; color: red; font-weight: bold;")
                else:
                    time_label.setText("—")
            vbox.addWidget(time_label)

    def calculate_time_text(self, task):
        if task.get("is_permanent"):
            return "П"
        elif task.get("no_deadline"):
            created = QDateTime.fromString(task.get("created_at"), "dd.MM.yyyy HH:mm")
            return f"{created.daysTo(QDateTime.currentDateTime())} д." if created.isValid() else "—"
        else:
            deadline = QDateTime.fromString(task.get("deadline"), "dd.MM.yyyy HH:mm")
            if deadline.isValid():
                diff = QDateTime.currentDateTime().daysTo(deadline)
                return f"ост. {diff} д." if diff >= 0 else f"проср. {abs(diff)} д."
            return "—"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            drag = QDrag(self)
            mime = QMimeData()
            mime.setText(json.dumps(self.task_data))
            drag.setMimeData(mime)
            drag.exec(Qt.DropAction.MoveAction)

    def mouseDoubleClickEvent(self, event):
        dialog = TaskInfoDialog(task_data=self.task_data, parent=self.main_window, on_edit_callback=self.on_edit_callback, status=self.panel_title)
        dialog.exec()


class TaskPanel(QFrame):
    def __init__(self, status, main_window=None, on_edit_callback=None):
        super().__init__()
        self.status = status
        self.main_window = main_window
        self.on_edit_callback = on_edit_callback
        self.setAcceptDrops(True)
        self.setStyleSheet("""
            background-color: rgba(255,255,255,0.1);
            border-radius: 15px;
        """)

        self.layout = QVBoxLayout(self)
        self.layout.addStretch()

    def dragEnterEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            task_data = json.loads(event.mimeData().text())
            self.add_task(task_data)
            self.main_window.move_task_to_panel(task_data, self.status)
            event.acceptProposedAction()

    def add_task(self, task_data):
        card = TaskCard(task_data, main_window=self.main_window, panel_title=self.status, on_edit_callback=self.on_edit_callback)
        self.layout.insertWidget(self.layout.count() - 1, card)


class TaskInfoDialog(QDialog):
    def __init__(self, task_data, parent=None, on_edit_callback=None, status=None):
        super().__init__(parent)
        self.task_data = task_data
        self.on_edit_callback = on_edit_callback
        self.status = status
        self.setWindowTitle(task_data.get("name", "Задача"))
        self.setModal(True)
        self.setFixedSize(500, 300)

        layout = QHBoxLayout(self)

        # Основной блок
        main_layout = QHBoxLayout()

        # Левая часть: ответственный + даты
        left_layout = QVBoxLayout()

        # Ответственный (аватар + имя)
        responsible_id = task_data.get("responsible")
        avatar_label = QLabel()
        avatar_label.setFixedSize(64, 64)

        responsible_name = "Не назначен"
        avatar_path = None
        if parent and hasattr(parent, "get_member_by_id"):
            member = parent.get_member_by_id(responsible_id)
            if member:
                responsible_name = member.get("name", "Неизвестно")
                avatar_path = member.get("avatar")

        if avatar_path and os.path.exists(avatar_path):
            pixmap = QPixmap(avatar_path).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio,
                                                 Qt.TransformationMode.SmoothTransformation)
            avatar_label.setPixmap(pixmap)
        else:
            avatar_label.setStyleSheet("border-radius: 32px; background-color: #ccc;")

        name_label = QLabel(responsible_name)
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        left_layout.addWidget(avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(name_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Время
        created_label = QLabel()
        deadline_label = QLabel()

        if task_data.get("is_permanent"):
            created_label.setText("Задача постоянная")
            deadline_label.hide()
        else:
            created = task_data.get("created_at", "—")
            created_label.setText(f"Создана: {created}")
            if not task_data.get("no_deadline"):
                deadline_label.setText(f"Дедлайн: {task_data.get('deadline', '—')}")
            else:
                deadline_label.setText("Без дедлайна")

        created_label.setStyleSheet("color: #ddd; font-size: 14px;")
        deadline_label.setStyleSheet("color: #ddd; font-size: 14px;")

        left_layout.addWidget(created_label)
        left_layout.addWidget(deadline_label)
        left_layout.addStretch()
        main_layout.addLayout(left_layout)

        # Правая часть (описание)
        right_frame = QFrame()
        right_layout = QVBoxLayout(right_frame)

        desc_label = QLabel("Описание:")
        desc_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")

        description = QTextBrowser()
        description.setOpenExternalLinks(True)
        description.setStyleSheet("background-color: #222; color: white; font-size: 14px;")

        html = task_data.get("description", "Нет описания")
        description.setHtml(html)
        description.setHtml(html)

        right_layout.addWidget(desc_label)
        right_layout.addWidget(description)
        main_layout.addWidget(right_frame)

        layout.addLayout(main_layout)

        # --- Кнопка редактирования ---
        edit_btn = QPushButton()
        edit_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/edit.png")))
        edit_btn.setIconSize(QSize(20, 20))
        edit_btn.setFixedSize(30, 30)
        edit_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        edit_btn.clicked.connect(self.edit_task)
        layout.addWidget(edit_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def edit_task(self):
        if self.on_edit_callback:
            self.on_edit_callback(self.task_data, self.status)
        self.close()


class AddTaskOverlay(QFrame):
    def __init__(self, parent=None, main_window=None, base_dir=None, task_data=None, status=None):
        super().__init__(parent)
        self.main_window = main_window
        self.base_dir = base_dir
        self.task_data = task_data
        self.edit_mode = False
        self.setGeometry(0, 0, main_window.width(), main_window.height())
        self.setStyleSheet("background-color: rgba(0, 0, 0, 160);")
        self.setVisible(True)
        self.raise_()

        files_map = {
            "Черновик": "draft_tasks.json",
            "В процессе": "progress_tasks.json",
            "Завершено": "finished_tasks.json",
            "Отложено": "delayed_tasks.json"
        }
        self.file = files_map[status] if status else None

        if self.task_data:
            self.edit_mode = True

        # Основной контейнер
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Панель
        panel = QFrame()
        panel.setFixedSize(1000, 625)
        panel.setStyleSheet("""
            background-color: #2a2a2a;
            border-radius: 20px;
            color: white;
        """)
        panel_layout = QVBoxLayout(panel)
        panel_layout.setSpacing(15)

        # Верхняя панель с кнопкой закрытия
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(32, 32)
        close_btn.setStyleSheet("""
            background-color: transparent;
            color: white;
            font-size: 18px;
            border: none;
        """)
        close_btn.clicked.connect(self.close_overlay)
        top_bar.addWidget(close_btn)
        panel_layout.addLayout(top_bar)

        # Заголовок
        title = QLabel("Создать задание")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 5px;")
        panel_layout.addWidget(title)

        # Контент: 2 колонки
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Левая колонка
        left_col = QVBoxLayout()
        left_col.setSpacing(15)

        # Название
        name_label = QLabel("Название задания")
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.task_name_input = QLineEdit()
        self.task_name_input.setPlaceholderText("Введите название...")
        self.task_name_input.setStyleSheet("""
            padding: 10px; font-size: 16px; border-radius: 10px;
            border: 1px solid #555; background-color: #3a3a3a; color: white;
        """)
        left_col.addWidget(name_label)
        left_col.addWidget(self.task_name_input)

        # Ответственный
        responsible_label = QLabel("Ответственный")
        responsible_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.task_responsible_combo = QComboBox()
        self.task_responsible_combo.setStyleSheet("""
            padding: 10px; font-size: 16px; border-radius: 10px;
            border: 1px solid #555; background-color: #3a3a3a; color: white;
        """)
        self.load_members_into_combo()
        left_col.addWidget(responsible_label)
        left_col.addWidget(self.task_responsible_combo)

        # Время
        datetime_style = """
            QDateTimeEdit {
                padding: 8px;
                font-size: 16px;
                border-radius: 10px;
                border: 1px solid #555;
                background-color: #3a3a3a;
                color: white;
            }
            QDateTimeEdit:disabled {
                background-color: #555;
                color: #aaa;
            }
            QCalendarWidget {
                background-color: #2a2a2a;
                color: white;
                border: 1px solid #555;
            }
            QCalendarWidget QToolButton {
                color: white;
                font-size: 16px;
            }
            QCalendarWidget QMenu {
                background-color: #3a3a3a;
                color: white;
            }
        """

        # Время создания
        date_start_label = QLabel("Дата создания")
        date_start_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.created_at_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.created_at_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.created_at_edit.setCalendarPopup(True)
        self.created_at_edit.setStyleSheet(datetime_style)
        left_col.addWidget(date_start_label)
        left_col.addWidget(self.created_at_edit)

        # Дедлайн
        date_end_label = QLabel("Дедлайн")
        date_end_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.deadline_edit = QDateTimeEdit(QDateTime.currentDateTime().addDays(1))
        self.deadline_edit.setDisplayFormat("dd.MM.yyyy HH:mm")
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setStyleSheet(datetime_style)
        left_col.addWidget(date_end_label)
        left_col.addWidget(self.deadline_edit)

        # Чекбоксы
        self.permanent_checkbox = QCheckBox("Постоянное задание")
        self.no_deadline_checkbox = QCheckBox("Задание без дедлайна")
        for cb in [self.permanent_checkbox, self.no_deadline_checkbox]:
            cb.setStyleSheet("""
                QCheckBox { font-size: 14px; color: white; }
                QCheckBox::indicator {
                    width: 18px; height: 18px;
                    border-radius: 3px; border: 2px solid white;
                    background-color: transparent;
                }
                QCheckBox::indicator:checked { background-color: white; }
            """)
        left_col.addWidget(self.permanent_checkbox)
        left_col.addWidget(self.no_deadline_checkbox)

        # Логика чекбоксов
        self.permanent_checkbox.stateChanged.connect(self.toggle_permanent_task)
        self.no_deadline_checkbox.stateChanged.connect(self.toggle_no_deadline_task)

        # Правая колонка
        right_col = QVBoxLayout()
        desc_label = QLabel("Описание задания")
        desc_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.task_description = QTextEdit()
        self.task_description.setPlaceholderText("Введите описание...")
        self.task_description.setStyleSheet("""
            padding: 10px; font-size: 16px; border-radius: 10px;
            border: 1px solid #555; background-color: #3a3a3a; color: white;
        """)
        right_col.addWidget(desc_label)
        right_col.addWidget(self.task_description)

        link_btn = QPushButton("🔗")
        link_btn.setFixedSize(40, 40)
        link_btn.setToolTip("Добавить ссылку")
        link_btn.clicked.connect(self.insert_link_into_description)
        right_col.addWidget(link_btn, alignment=Qt.AlignmentFlag.AlignRight)

        # Объединяем колонки
        content_layout.addLayout(left_col, 1)
        content_layout.addLayout(right_col, 2)
        panel_layout.addLayout(content_layout)

        # Заполнение данных при редактировании
        if self.edit_mode and self.task_data:
            self.task_name_input.setText(self.task_data.get("name", ""))
            self.task_description.setHtml(self.task_data.get("description", ""))

            # Ответственный
            responsible_id = self.task_data.get("responsible")
            if responsible_id:
                idx = self.task_responsible_combo.findData(responsible_id)
                if idx >= 0:
                    self.task_responsible_combo.setCurrentIndex(idx)

            # Чекбоксы
            self.permanent_checkbox.setChecked(self.task_data.get("is_permanent", False))
            self.no_deadline_checkbox.setChecked(self.task_data.get("no_deadline", False))

            # Даты
            if self.task_data.get("created_at"):
                self.created_at_edit.setDateTime(QDateTime.fromString(self.task_data["created_at"], "dd.MM.yyyy HH:mm"))
            if self.task_data.get("deadline"):
                self.deadline_edit.setDateTime(QDateTime.fromString(self.task_data["deadline"], "dd.MM.yyyy HH:mm"))

        # Определение кнопок при режиме создания и редактирования задания
        if not self.edit_mode:
            create_btn = QPushButton("Создать задание")
            create_btn.setStyleSheet("""
                background-color: #4CAF50; color: white; font-size: 18px;
                font-weight: bold; border: none; border-radius: 12px;
                padding: 10px; margin-top: 5px;
            """)
            create_btn.clicked.connect(self.create_new_task)
            panel_layout.addWidget(create_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            # Горизонтальный контейнер для кнопок
            btn_layout = QHBoxLayout()
            btn_layout.setSpacing(15)
            btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            save_btn = QPushButton("Сохранить изменения")
            save_btn.setStyleSheet("""
                background-color: #4385AB; color: white; font-size: 18px;
                font-weight: bold; border: none; border-radius: 12px;
                padding: 10px;
            """)
            save_btn.clicked.connect(self.save_task)
            btn_layout.addWidget(save_btn)

            delete_btn = QPushButton("Удалить задание")
            delete_btn.setStyleSheet("""
                background-color: #E62525; color: white; font-size: 18px;
                font-weight: bold; border: none; border-radius: 12px;
                padding: 10px;
            """)
            delete_btn.clicked.connect(self.delete_task)
            btn_layout.addWidget(delete_btn)

            # Добавляем оба рядом
            panel_layout.addLayout(btn_layout)

        layout.addWidget(panel)

    def load_members_into_combo(self):
        json_path = os.path.join(base_dir, "db/members.json")
        self.task_responsible_combo.clear()
        self.members_map = {}  # {name: id}

        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                members = json.load(f)
                for member in members:
                    name = member["name"]
                    member_id = member.get("id")
                    self.members_map[name] = member_id
                    self.task_responsible_combo.addItem(name, member_id)

    def toggle_permanent_task(self, state):
        if state == Qt.CheckState.Checked:
            # Блокируем оба поля
            self.created_at_edit.setEnabled(False)
            self.deadline_edit.setEnabled(False)
            # Снимаем другой чекбокс
            self.no_deadline_checkbox.blockSignals(True)
            self.no_deadline_checkbox.setChecked(False)
            self.no_deadline_checkbox.blockSignals(False)
        else:
            # Разблокируем оба
            self.created_at_edit.setEnabled(True)
            self.deadline_edit.setEnabled(True)

    def toggle_no_deadline_task(self, state):
        if state == Qt.CheckState.Checked:
            # Блокируем только дедлайн
            self.deadline_edit.setEnabled(False)
            # Снимаем другой чекбокс
            self.permanent_checkbox.blockSignals(True)
            self.permanent_checkbox.setChecked(False)
            self.permanent_checkbox.blockSignals(False)
            # При этом created_at остается активным
        else:
            # Разблокируем дедлайн, если не включен permanent
            if not self.permanent_checkbox.isChecked():
                self.deadline_edit.setEnabled(True)

    def insert_link_into_description(self):
        cursor = self.task_description.textCursor()
        selected_text = cursor.selectedText()
        if not selected_text:
            return  # Ничего не выделено

        url, ok = QInputDialog.getText(self, "Добавить ссылку", "Введите URL:")
        if ok and url:
            # Создаем HTML-ссылку
            html_link = f'<a href="{url}">{selected_text}</a>'
            cursor.insertHtml(html_link)

    def create_new_task(self):
        task_name = self.task_name_input.text().strip()

        # 1. Проверка на пустое имя
        if not task_name:
            QMessageBox.warning(self, "Ошибка", "Имя задания обязательно!")
            return

        # 2. Проверка на оба чекбокса
        if self.permanent_checkbox.isChecked() and self.no_deadline_checkbox.isChecked():
            QMessageBox.warning(self, "Ошибка",
                                "Нельзя одновременно выбрать 'Постоянное задание' и 'Задание без дедлайна'.")
            return

        # 3. Проверка на дедлайн >= дата создания (только если поля активны)
        if not self.permanent_checkbox.isChecked() and not self.no_deadline_checkbox.isChecked():
            created_dt = self.created_at_edit.dateTime()
            deadline_dt = self.deadline_edit.dateTime()
            if deadline_dt < created_dt:
                QMessageBox.warning(self, "Ошибка", "Дедлайн не может быть раньше даты создания.")
                return

        # 4. Генерация ID
        def generate_unique_id():
            all_task_files = [
                os.path.join(base_dir, "db/tasks/draft_tasks.json"),
                os.path.join(base_dir, "db/tasks/progress_tasks.json"),
                os.path.join(base_dir, "db/tasks/finished_tasks.json"),
                os.path.join(base_dir, "db/tasks/delayed_tasks.json")
            ]

            while True:
                new_id = str(uuid.uuid4())
                if not any(task.get("id") == new_id for file_path in all_task_files if os.path.exists(file_path)
                           for task in json.load(open(file_path, "r", encoding="utf-8"))):
                    return new_id
        new_task_id = generate_unique_id()

        # 5. Загружаем существующие задания
        tasks_path = os.path.join(base_dir, "db/tasks/draft_tasks.json")
        tasks = []
        if os.path.exists(tasks_path):
            with open(tasks_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)

        # 6. Формируем данные задания
        responsible_name = self.task_responsible_combo.currentText()
        if not responsible_name:
            QMessageBox.warning(self, "Ошибка", "Обязан быть ответственный за задание!")
            return
        responsible_id = self.members_map.get(responsible_name)

        task_data = {
            "id": new_task_id,
            "name": task_name,
            "responsible": responsible_id,
            "description": self.task_description.toHtml(),
            "created_at": None if self.permanent_checkbox.isChecked() else self.created_at_edit.dateTime().toString(
                "dd.MM.yyyy HH:mm"),
            "deadline": None if self.no_deadline_checkbox.isChecked() or self.permanent_checkbox.isChecked()
            else self.deadline_edit.dateTime().toString("dd.MM.yyyy HH:mm"),
            "is_permanent": self.permanent_checkbox.isChecked(),
            "no_deadline": self.no_deadline_checkbox.isChecked(),
        }

        # 7. Сохраняем
        tasks.append(task_data)
        with open(tasks_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

        if self.main_window and hasattr(self.main_window, "load_tasks_into_panels"):
            self.main_window.update_members_tasks_count()
            self.main_window.refresh_members_list()
            self.main_window.load_tasks_into_panels()

        QMessageBox.information(self, "Успех", "Задание создано!")
        self.close_overlay()

    def save_task(self):
        # Обновляем данные
        self.task_data["name"] = self.task_name_input.text().strip()
        self.task_data["description"] = self.task_description.toHtml()
        self.task_data["responsible"] = self.task_responsible_combo.currentData()
        self.task_data["is_permanent"] = self.permanent_checkbox.isChecked()
        self.task_data["no_deadline"] = self.no_deadline_checkbox.isChecked()
        self.task_data["created_at"] = None if self.permanent_checkbox.isChecked() else \
            self.created_at_edit.dateTime().toString("dd.MM.yyyy HH:mm")
        self.task_data[
            "deadline"] = None if self.no_deadline_checkbox.isChecked() or self.permanent_checkbox.isChecked() \
            else self.deadline_edit.dateTime().toString("dd.MM.yyyy HH:mm")

        # Сохраняем изменения в файле
        file_path = os.path.join(self.base_dir, f"db/tasks/{self.file}")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                tasks = json.load(f)
            for idx, t in enumerate(tasks):
                if t["id"] == self.task_data["id"]:
                    tasks[idx] = self.task_data
                    break
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=4)

        self.main_window.update_members_tasks_count()
        self.main_window.load_tasks_into_panels()
        QMessageBox.information(self, "Успех", "Изменения сохранены!")
        self.close_overlay()

    def delete_task(self):
        reply = QMessageBox.question(self, "Подтверждение", "Удалить это задание?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            file_path = os.path.join(self.base_dir, f"db/tasks/{self.file}")
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    tasks = json.load(f)
                tasks = [t for t in tasks if t["id"] != self.task_data["id"]]
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(tasks, f, ensure_ascii=False, indent=4)

            self.main_window.update_members_tasks_count()
            self.main_window.refresh_members_list()
            self.main_window.load_tasks_into_panels()
            QMessageBox.information(self, "Удалено", "Задача удалена!")
            self.close_overlay()

    def close_overlay(self):
        self.setVisible(False)
        self.deleteLater()


class MemberInfoDialog(QDialog):
    def __init__(self, main_window, member, on_edit_callback=None):
        super().__init__()
        self.main_window = main_window
        self.setWindowTitle("Информация об участнике")
        self.setModal(True)
        self.setFixedSize(300, 400)
        self.member = member
        self.on_edit_callback = on_edit_callback

        layout = QVBoxLayout(self)

        # --- Аватар ---
        avatar_label = QLabel()
        avatar_label.setFixedSize(100, 100)
        if member.get("avatar") and os.path.exists(member["avatar"]):
            pixmap = QPixmap(member["avatar"]).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                                      Qt.TransformationMode.SmoothTransformation)
            avatar_label.setPixmap(pixmap)
        else:
            avatar_label.setStyleSheet("background-color: #444; border-radius: 50px;")
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(avatar_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Имя ---
        name_label = QLabel(member.get("name", "Без имени"))
        name_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        # --- Должность ---
        post = member.get("post", "Отсутствует")
        post_color = "#888888"
        if post != "Отсутствует":
            post_color = self.main_window.get_post_color(post)
        post_label = QLabel(post)
        post_label.setStyleSheet(f"color: {post_color}; font-size: 18px;")
        post_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(post_label)

        # --- Статус ---
        status = member.get("status", "Неизвестно")
        status_label = QLabel(f"Статус: {status}")
        status_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(status_label)

        # --- Кол-во дел ---
        tasks_label = QLabel(f"Количество задач: {member.get('tasks', 0)}")
        tasks_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(tasks_label)

        # --- Ссылки ---
        links_label = QLabel("Ссылки:")
        links_label.setStyleSheet("color: white; font-size: 16px;")
        layout.addWidget(links_label)
        for link in member.get("links", []):
            if link:
                link_btn = QPushButton(link)
                link_btn.setStyleSheet("color: #00aaff; text-align: left;")
                link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                link_btn.clicked.connect(lambda _, l=link: QDesktopServices.openUrl(QUrl(l)))
                layout.addWidget(link_btn)

        layout.addStretch()

        # --- Кнопки ---
        btn_layout = QHBoxLayout()
        edit_btn = QPushButton()
        edit_icon = QIcon(os.path.join(base_dir, "db/images/interface/edit.png"))
        edit_btn.setIcon(edit_icon)
        edit_btn.setFixedSize(30, 30)
        edit_btn.setFlat(True)
        btn_layout.addWidget(edit_btn)
        layout.addLayout(btn_layout)

        edit_btn.clicked.connect(self.edit_member)

    def edit_member(self):
        if self.on_edit_callback:
            self.on_edit_callback(self.member)
        self.close()


class AddMemberOverlay(QFrame):
    def __init__(self, main_window, json_path, on_close=None, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.on_close = on_close
        self.json_path = json_path
        self.edit_mode = False
        self.editing_member_id = None
        self.setObjectName("addMemberOverlay")
        self.setStyleSheet("""
            QFrame#addMemberOverlay {
                background-color: rgba(0, 0, 0, 230);
                border: none;
            }
        """)
        self.setVisible(False)

        # Центральная панель
        self.panel = QFrame()
        self.panel.setFixedSize(800, 600)
        self.panel.setObjectName("addPeoplePanel")
        self.panel.setStyleSheet("""
            QFrame#addPeoplePanel {
                background-color: black;
                border: 2px solid white;
                border-radius: 15px;
            }
        """)

        # Основной лейаут (центрируем содержимое)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(15)

        # Заголовок + кнопка закрытия
        top_bar = QHBoxLayout()
        title = QLabel("Добавить участника")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        top_bar.addWidget(title)
        top_bar.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.clicked.connect(self.close_overlay)
        top_bar.addWidget(close_btn)
        panel_layout.addLayout(top_bar)

        # --- Аватар ---
        self.avatar_btn = QPushButton("Выбрать аватар")
        self.avatar_btn.clicked.connect(self.select_avatar)
        panel_layout.addWidget(self.avatar_btn)

        self.avatar_preview = QLabel("Нет аватара")
        self.avatar_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar_preview.setFixedSize(120, 120)
        self.avatar_preview.setStyleSheet("border: 1px solid #ccc; background-color: #f5f5f5; color: white;")
        panel_layout.addWidget(self.avatar_preview, alignment=Qt.AlignmentFlag.AlignCenter)

        # --- Имя ---
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Никнейм / Имя (обязательно)")
        panel_layout.addWidget(self.name_input)

        # --- Должность ---
        post_label = QLabel("Должность:")
        post_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        panel_layout.addWidget(post_label)

        self.post_combo = QComboBox()
        self.post_combo.addItem("Нет")  # Должность необязательна
        self.load_positions()  # загружаем должности из файла
        panel_layout.addWidget(self.post_combo)

        # --- Статус ---
        status_label = QLabel("Статус:")
        status_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        panel_layout.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Доступен", "Занят", "Неизвестно"])
        panel_layout.addWidget(self.status_combo)

        # --- Ссылки ---
        self.link1_input = QLineEdit()
        self.link1_input.setPlaceholderText("Ссылка 1 (обязательно)")
        panel_layout.addWidget(self.link1_input)

        self.link2_input = QLineEdit()
        self.link2_input.setPlaceholderText("Ссылка 2 (необязательно)")
        panel_layout.addWidget(self.link2_input)

        self.link3_input = QLineEdit()
        self.link3_input.setPlaceholderText("Ссылка 3 (необязательно)")
        panel_layout.addWidget(self.link3_input)

        # --- Кнопки ---
        self.btns_layout = QHBoxLayout()

        # Кнопка сохранения
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_member)
        self.btns_layout.addWidget(save_btn)

        # Кнопка удаления
        self.delete_btn = QPushButton("Удалить")
        self.delete_btn.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.delete_btn.clicked.connect(self.delete_member)
        self.btns_layout.addWidget(self.delete_btn)

        # Кнопка отмены
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.close_overlay)
        self.btns_layout.addWidget(self.cancel_btn)

        panel_layout.addLayout(self.btns_layout)
        layout.addWidget(self.panel)

        self.avatar_path = None  # путь к аватару
        self.json_path = os.path.join(os.path.dirname(__file__), "db/members.json")

    def load_positions(self):
        self.post_combo.clear()  # Очистка списка перед обновлением
        json_path = os.path.join(os.path.dirname(__file__), "db/positions.json")
        if os.path.exists(json_path):
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f).get("positions", [])
                for pos in data:
                    self.post_combo.addItem(pos["name"])

    def select_avatar(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Выберите аватар", "", "Изображения (*.png *.jpg *.jpeg)")
        if file_name:
            self.avatar_path = file_name
            pixmap = QPixmap(file_name).scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            self.avatar_preview.setPixmap(pixmap)

    def save_member(self):
        name = self.name_input.text().strip()
        link1 = self.link1_input.text().strip()

        if not name or not link1:
            QMessageBox.warning(self, "Ошибка", "Имя и Ссылка 1 обязательны!")
            return

        # Чтение текущего списка
        members = []
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                members = json.load(f)  # теперь список, а не словарь

        if hasattr(self, "editing_member_id") and self.editing_member_id:  # Редактируем существующего пользователя
            for m in members:
                if m["id"] == self.editing_member_id:
                    m.update({
                        "name": name,
                        "post": self.post_combo.currentText() if self.post_combo.currentText() != "Нет" else None,
                        "status": self.status_combo.currentText(),
                        "avatar": self.avatar_path,
                        "links": [link1, self.link2_input.text().strip(), self.link3_input.text().strip()]
                    })
                    break
            QMessageBox.information(self, "Успех", f"Данные участника '{name}' изменены.")
        else:  # Добавляем нового человека
            # Проверяем, есть ли участник с таким именем
            if any(member.get("name") == name for member in members):
                QMessageBox.warning(self, "Ошибка", f"Участник с именем '{name}' уже существует!")
                return

            unique_id = str(uuid.uuid4())
            member_data = {
                "id": unique_id,
                "name": name,
                "post": self.post_combo.currentText() if self.post_combo.currentText() != "Нет" else None,
                "status": self.status_combo.currentText(),
                "tasks": 0,
                "avatar": self.avatar_path,
                "links": [link1, self.link2_input.text().strip(), self.link3_input.text().strip()]
            }
            members.append(member_data)

            QMessageBox.information(self, "Успех", "Участник добавлен!")

        # Сохраняем в JSON
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=4)

        # Обновляем панель участников
        if self.main_window and hasattr(self.main_window, "refresh_members_list"):
            self.main_window.update_members_tasks_count()
            self.main_window.refresh_members_list()

        # Очищаем поля
        self.clear_form()
        self.close_overlay()

    def delete_member(self):
        if not self.editing_member_id:
            QMessageBox.warning(self, "Ошибка", "Невозможно удалить: ID не найден.")
            return

        # Загружаем участников
        members = []
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                members = json.load(f)

        # Ищем участника
        for member in members:
            if member["id"] == self.editing_member_id:
                if member.get("tasks", 0) > 0:
                    QMessageBox.warning(self, "Ошибка", "Нельзя удалить участника с активными задачами!")
                    return
                members.remove(member)
                break

        # Сохраняем изменения
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(members, f, ensure_ascii=False, indent=4)

        QMessageBox.information(self, "Успех", "Участник удалён.")

        # Обновляем интерфейс
        if self.main_window and hasattr(self.main_window, "refresh_members_list"):
            self.main_window.refresh_members_list()

        self.close_overlay()

    def load_member(self, member):
        self.editing_member_id = member.get("id")
        self.name_input.setText(member.get("name", ""))
        self.status_combo.setCurrentText(member.get("status", "Доступен"))
        self.post_combo.setCurrentText(member.get("post", "Нет"))
        self.avatar_path = member.get("avatar")
        if self.avatar_path and os.path.exists(self.avatar_path):
            self.avatar_preview.setPixmap(QPixmap(self.avatar_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))
        links = member.get("links", [])
        self.link1_input.setText(links[0] if len(links) > 0 else "")
        self.link2_input.setText(links[1] if len(links) > 1 else "")
        self.link3_input.setText(links[2] if len(links) > 2 else "")

    def clear_form(self):
        self.avatar_path = None
        self.avatar_preview.setText("Нет аватара")
        self.avatar_preview.setPixmap(QPixmap())
        self.name_input.clear()
        self.status_combo.setCurrentIndex(0)
        self.link1_input.clear()
        self.link2_input.clear()
        self.link3_input.clear()

    def show_overlay(self):
        """Выполняет две функции:
            Настраивает показ кнопок Удалить и Отмена в карточке создания/редактирования участника.
            Показывает и растягивает на размер родителя
        """
        if self.edit_mode:
            self.cancel_btn.hide()
            self.delete_btn.show()
        else:
            self.delete_btn.hide()
            self.cancel_btn.show()

        if self.main_window:
            self.setGeometry(0, 0, self.main_window.width(), self.main_window.height())
        self.setVisible(True)
        self.raise_()

    def close_overlay(self):
        """Закрыть и вызвать callback, если есть"""
        self.edit_mode = False
        self.editing_member_id = None
        self.clear_form()
        self.setVisible(False)
        if self.on_close:
            self.on_close()


class HoverButton(QPushButton):
    def __init__(self, icon_default, icon_active, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.btn_default = icon_default
        self.btn_active = icon_active
        self.setIcon(self.btn_default)
        self.setIconSize(QSize(30, 30))
        self.setStyleSheet("border: none; background: transparent;")
        self.setFixedSize(40, 40)
        self.panel_open = False  # флаг состояния панели

        # Анимация масштаба
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)  # скорость анимации (мс)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)  # плавность

    def enterEvent(self, event):
        if not self.panel_open:
            self.setIcon(self.btn_active)
        # Увеличиваем кнопку
        rect = self.geometry()
        self.animation.stop()
        self.animation.setStartValue(rect)
        self.animation.setEndValue(rect.adjusted(-2, -2, 2, 2))  # чуть больше
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.panel_open:
            self.setIcon(self.btn_default)
        # Возвращаем размер
        rect = self.geometry()
        self.animation.stop()
        self.animation.setStartValue(rect)
        self.animation.setEndValue(rect.adjusted(2, 2, -2, -2))  # исходный размер
        self.animation.start()
        super().leaveEvent(event)

    def setPanelState(self, open_state):
        self.panel_open = open_state
        if self.panel_open:
            self.setIcon(self.btn_active)
        else:
            self.setIcon(self.btn_default)


class SettingsPanel(QFrame):
    def __init__(self, parent, on_close, on_change_background, on_edit_positions):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(30, 30, 30, 230); color: white;")
        self.setFixedWidth(300)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)

        # Верхняя строка с крестиком
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("border: none; color: white; font-size: 18px;")
        close_btn.clicked.connect(on_close)
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)

        # Кнопка редактирования должностей
        edit_positions_btn = QPushButton("Редактировать должности")
        edit_positions_btn.setStyleSheet("background-color: #444; color: white; padding: 10px;")
        edit_positions_btn.clicked.connect(on_edit_positions)
        layout.addWidget(edit_positions_btn)

        # Кнопка смены фона
        change_bg_btn = QPushButton("Сменить фон")
        change_bg_btn.setStyleSheet("background-color: #444; color: white; padding: 10px;")
        change_bg_btn.clicked.connect(on_change_background)
        layout.addWidget(change_bg_btn)

        layout.addWidget(change_bg_btn)
        layout.addStretch()

        self.setLayout(layout)


class EditPositionsOverlay(QFrame):
    # Баг - если создать новую должность, она появится только после перезапуска программы
    def __init__(self, parent=None, main_window=None, json_path="db/positions.json"):
        super().__init__(parent)
        self.main_window = main_window
        self.json_path = json_path
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.setVisible(False)

        # Загружаем позиции
        self.positions = self.load_positions()

        # Главный лейаут (оверлей)
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Панель
        self.panel = QFrame()
        self.panel.setFixedSize(800, 600)
        self.panel.setObjectName("editPositionsPanel")
        self.panel.setStyleSheet("""
            QFrame#editPositionsPanel {
                background-color: black;
                border: 2px solid white;
                border-radius: 15px;
            }
        """)
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(15, 2, 15, 2)

        # Верхняя строка с заголовком и крестиком
        header_layout = QHBoxLayout()
        title = QLabel("Редактировать должности")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: white;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("border: none; font-size: 22px; color: white;")
        close_btn.clicked.connect(self.hide_overlay)
        header_layout.addWidget(close_btn)
        panel_layout.addLayout(header_layout)

        # Список должностей
        self.positions_container = QWidget()
        self.positions_layout = QVBoxLayout(self.positions_container)
        self.positions_layout.setContentsMargins(0, 0, 0, 0)
        self.positions_layout.setSpacing(5)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.positions_container)
        self.scroll_area.setFixedHeight(200)  # Высота с прокруткой

        panel_layout.addWidget(self.scroll_area)

        # Поле ввода + кнопка добавления
        input_layout = QHBoxLayout()
        self.position_input = QLineEdit()
        self.position_input.setPlaceholderText("Введите должность...")
        self.position_input.setStyleSheet("border: none; font-size: 22px; color: white;")
        add_btn = QPushButton()
        add_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/add.png")))
        add_btn.setIconSize(QSize(30, 30))
        add_btn.setFixedSize(30, 30)
        add_btn.setStyleSheet("border: none;")
        add_btn.clicked.connect(self.add_position)
        input_layout.addWidget(self.position_input)
        input_layout.addWidget(add_btn)
        panel_layout.addLayout(input_layout)

        overlay_layout.addWidget(self.panel)

        self.refresh_list()

    def load_positions(self):
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                data = json.load(f).get("positions", [])
                # Конвертация старого формата (строки -> словари)
                return [{"name": pos, "color": "#FFFFFF"} if isinstance(pos, str) else pos for pos in data]
        return []

    def save_positions(self):
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump({"positions": self.positions}, f, ensure_ascii=False, indent=4)

    def refresh_list(self):
        # Очистим список
        for i in reversed(range(self.positions_layout.count())):
            widget = self.positions_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Добавим все должности
        for idx, pos in enumerate(self.positions):
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)

            # Текст должности
            label = QLabel(pos["name"])
            label.setStyleSheet(f"font-size: 22px; color: {pos['color']}")
            row_layout.addWidget(label)

            # Кнопка выбора цвета
            color_btn = QPushButton()
            color_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/color.png")))  # Иконка палитры
            color_btn.setIconSize(QSize(20, 20))
            color_btn.setFixedSize(30, 30)
            color_btn.setStyleSheet("border: none;")
            color_btn.clicked.connect(lambda _, i=idx: self.change_color(i))
            row_layout.addWidget(color_btn)

            # Кнопка редактирования
            edit_btn = QPushButton()
            edit_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/edit.png")))
            edit_btn.setIconSize(QSize(20, 20))
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet("border: none;")
            edit_btn.clicked.connect(lambda _, x=idx: self.edit_position(x))
            row_layout.addWidget(edit_btn)

            # Кнопка удаления
            del_btn = QPushButton()
            del_btn.setIcon(QIcon(os.path.join(base_dir, "db/images/interface/delete.png")))
            del_btn.setIconSize(QSize(20, 20))
            del_btn.setFixedSize(30, 30)
            del_btn.setStyleSheet("border: none;")
            del_btn.clicked.connect(lambda _, x=idx: self.delete_position(x))
            row_layout.addWidget(del_btn)

            self.positions_layout.addWidget(row)

    def add_position(self):
        new_pos = self.position_input.text().strip()
        if new_pos and all(pos["name"] != new_pos for pos in self.positions):
            self.positions.append({"name": new_pos, "color": "#FFFFFF"})
            self.save_positions()
            self.refresh_list()
            self.position_input.clear()
            if self.main_window and hasattr(self.main_window, "refresh_positions_everywhere"):
                self.main_window.refresh_positions_everywhere()
        else:
            QMessageBox.warning(self, "Ошибка", "Такая должность уже есть или поле пустое!")

    def edit_position(self, index):
        row_widget = self.positions_layout.itemAt(index).widget()
        for i in range(row_widget.layout().count()):
            widget = row_widget.layout().itemAt(i).widget()
            if isinstance(widget, QLabel):
                text = widget.text()
                widget.deleteLater()
                editor = QLineEdit(text)
                editor.setStyleSheet("""
                    font-size: 22px;
                    padding: 4px;
                """)
                layout = row_widget.layout()
                if layout is not None:
                    layout.insertWidget(0, editor)
                editor.returnPressed.connect(lambda: self.save_edited_position(index, editor))
                self.main_window.refresh_members_list()
                editor.setFocus()
                break

    def save_edited_position(self, index, editor):
        new_text = editor.text().strip()
        current_text = self.positions[index]["name"]

        # Проверка: либо имя не пустое и не дублирует чужие
        if new_text and (new_text == current_text or all(
                pos["name"] != new_text for i, pos in enumerate(self.positions) if i != index)):

            # 1. Обновляем имя должности в positions.json
            self.positions[index]["name"] = new_text
            self.save_positions()

            # 2. Обновляем должность у участников в members.json
            members_path = os.path.join(base_dir, "db/members.json")
            if os.path.exists(members_path):
                with open(members_path, "r", encoding="utf-8") as f:
                    members = json.load(f)

                # Заменяем должность у всех участников, у кого была старая
                for member in members:
                    if member.get("post") == current_text:
                        member["post"] = new_text

                with open(members_path, "w", encoding="utf-8") as f:
                    json.dump(members, f, ensure_ascii=False, indent=4)

            # 3. Обновляем интерфейс и ComboBox
            self.refresh_list()
            if self.main_window and hasattr(self.main_window, "refresh_positions_everywhere"):
                self.main_window.refresh_positions_everywhere()
        else:
            QMessageBox.warning(self, "Ошибка", "Название пустое или уже существует!")

    def change_color(self, index):
        current_color = self.positions[index]["color"]
        color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет должности")
        if color.isValid():
            self.positions[index]["color"] = color.name()
            self.save_positions()
            self.refresh_list()
            if self.main_window and hasattr(self.main_window, "refresh_positions_everywhere"):
                self.main_window.refresh_positions_everywhere()

    def delete_position(self, index):
        position_name = self.positions[index]["name"]
        print(position_name)

        # Путь к members.json (или где хранятся участники)
        members_path = os.path.join(base_dir, "db/members.json")
        if os.path.exists(members_path):
            with open(members_path, "r", encoding="utf-8") as f:
                members = json.load(f)

            # Проверяем, есть ли участник с этой должностью
            in_use = any(m.get("post") == position_name for m in members)
            print(in_use)
            if in_use:
                QMessageBox.warning(self, "Ошибка", f"Невозможно удалить должность '{position_name}', "
                                                    f"так как она назначена участникам.")
                return  # Выходим, не удаляем
        # Если должность не используется, удаляем
        del self.positions[index]
        self.save_positions()
        self.refresh_list()
        if self.main_window and hasattr(self.main_window, "refresh_positions_everywhere"):
            self.main_window.refresh_positions_everywhere()

    def show_overlay(self):
        self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.setVisible(True)
        self.raise_()

    def hide_overlay(self):
        self.setVisible(False)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
