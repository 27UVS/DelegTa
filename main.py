import os
import sys
import json
import uuid

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QDialog,
    QFileDialog, QFrame, QLineEdit, QMessageBox, QScrollArea, QColorDialog, QComboBox, QSizePolicy
)
from PySide6.QtGui import QPixmap, QIcon, QColor, QDesktopServices
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QSettings, QSize, QEasingCurve, QUrl

base_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DelegTa")
        self.setWindowIcon(QIcon(os.path.join(base_dir, "images/interface/icon.png")))
        # icon author: https://vk.com/forgottenandunknownman
        self.json_path = os.path.join(os.path.dirname(__file__), "members.json")

        # --- Загружаем сохранённый фон ---
        self.settings = QSettings("MyCompany", "DelegTaApp")
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
        self.btn_active = QIcon(os.path.join(base_dir, "images/interface/settings_active.png"))
        # source: https://www.flaticon.com/ru/free-icon/settings_807390
        self.btn_default = QIcon(os.path.join(base_dir, "images/interface/settings_default.png"))
        # source: https://www.flaticon.com/ru/free-icon/settings_807313

        self.settings_btn = HoverButton(self.btn_default, self.btn_active, self)
        self.settings_btn.clicked.connect(self.toggle_settings_panel)
        # self.settings_btn.raise_()

        # --- Основной контент ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Основная область с панелями
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

        #  Заголовок
        header_layout = QHBoxLayout()
        title_label = QLabel("Участники")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)

        #  Кнопка
        btn_add = os.path.join(base_dir, "images/interface/add.png")
        # source: https://www.flaticon.com/ru/free-icon/add_3363871
        self.add_member_overlay = AddMemberOverlay(self, json_path=os.path.join(base_dir, "members.json"))
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

        # Область прокрутки
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
        self.refresh_members_list()
        content_layout.addWidget(self.members_panel)

        # Правая часть с задачами
        tasks_container = QVBoxLayout()
        tasks_container.setContentsMargins(5, 40, 5, 5)

        # Строка из 4 панелей
        tasks_row = QHBoxLayout()
        tasks_row.setSpacing(15)

        # Панели задач
        self.columns = []
        colors = {
            "Черновик": "rgba(62, 95, 138, 220)",
            "В процессе": "rgba(229, 81, 55, 220)",
            "Завершено": "rgba(154, 205, 50, 220)",
            "Отложено": "rgba(102, 0, 102, 220)"
        }
        titles = ["Черновик", "В процессе", "Завершено", "Отложено"]

        for title in titles:
            panel = QFrame()
            panel.setStyleSheet(f"""
                background-color: {colors[title]};
                border-radius: 20px;
                border: 1px solid #ccc;
            """)

            vbox = QVBoxLayout()
            vbox.setContentsMargins(10, 10, 10, 10)

            # Заголовок (белая область)
            header = QLabel(title)
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header.setStyleSheet("""
                background-color: white;
                color: #333;
                font-size: 18px;
                font-weight: bold;
                border-radius: 10px;  /* скругление только у заголовка */
                padding: 8px;
            """)

            vbox.addWidget(header)
            vbox.addStretch()
            panel.setLayout(vbox)
            tasks_row.addWidget(panel)
            self.columns.append(panel)

        tasks_container.addLayout(tasks_row)
        content_layout.addLayout(tasks_container)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # --- Панель настроек ---
        self.edit_positions_overlay = EditPositionsOverlay(self)
        self.settings_panel = SettingsPanel(
            self,
            on_close=self.toggle_settings_panel,
            on_change_background=self.change_background,
            on_edit_positions=EditPositionsOverlay(self).show_overlay
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

        json_path = os.path.join(os.path.dirname(__file__), "members.json")
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

    @staticmethod
    def get_post_color(post_name):
        positions_path = os.path.join(base_dir, "positions.json")
        if os.path.exists(positions_path):
            with open(positions_path, "r", encoding="utf-8") as f:
                positions = json.load(f).get("positions", [])
                for pos in positions:
                    if pos["name"] == post_name:
                        return pos.get("color", "#FFFFFF")
        return "#FFFFFF"

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
        self.add_member_overlay.load_member(member)
        self.add_member_overlay.show_overlay()


class MemberInfoDialog(QDialog):
    def __init__(self, parent, member, on_edit_callback=None):
        super().__init__(parent)
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
            post_color = parent.get_post_color(post)
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
        edit_icon = QIcon(os.path.join(base_dir, "images/interface/edit.png"))
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
    def __init__(self, parent, json_path, on_close=None):
        super().__init__(parent)
        self.on_close = on_close
        self.json_path = json_path
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

        # Ссылки
        self.link1_input = QLineEdit()
        self.link1_input.setPlaceholderText("Ссылка 1 (обязательно)")
        panel_layout.addWidget(self.link1_input)

        self.link2_input = QLineEdit()
        self.link2_input.setPlaceholderText("Ссылка 2 (необязательно)")
        panel_layout.addWidget(self.link2_input)

        self.link3_input = QLineEdit()
        self.link3_input.setPlaceholderText("Ссылка 3 (необязательно)")
        panel_layout.addWidget(self.link3_input)

        # Кнопки
        btns_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_member)
        btns_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.close_overlay)
        btns_layout.addWidget(cancel_btn)
        panel_layout.addLayout(btns_layout)

        layout.addWidget(self.panel)

        self.avatar_path = None  # путь к аватару
        self.json_path = os.path.join(os.path.dirname(__file__), "members.json")

    def load_positions(self):
        json_path = os.path.join(os.path.dirname(__file__), "positions.json")
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
        if self.parent() and hasattr(self.parent(), "refresh_members_list"):
            self.parent().refresh_members_list()

        # Очищаем поля
        self.clear_form()
        self.close_overlay()

    def load_member(self, member):
        self.clear_form()
        self.editing_member_id = member.get("id")
        self.name_input.setText(member.get("name", ""))
        self.status_combo.setCurrentText(member.get("status", "Доступен"))
        self.post_combo.setCurrentText(member.get("post", "Нет"))
        self.avatar_path = member.get("avatar")
        if self.avatar_path and os.path.exists(self.avatar_path):
            self.avatar_preview.setPixmap(QPixmap(self.avatar_path).scaled(80, 80, Qt.KeepAspectRatio))
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
        """Показываем и растягиваем на размер родителя"""
        if self.parent():
            self.setGeometry(0, 0, self.parent().width(), self.parent().height())
        self.setVisible(True)
        self.raise_()

    def close_overlay(self):
        """Закрыть и вызвать callback, если есть"""
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
        edit_positions_btn.clicked.connect(on_edit_positions)  # ✅ теперь чисто и безопасно
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
    def __init__(self, parent=None, json_path="positions.json"):
        super().__init__(parent)
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
        add_btn.setIcon(QIcon(os.path.join(base_dir, "images/interface/add.png")))
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
            color_btn.setIcon(QIcon(os.path.join(base_dir, "images/interface/color.png")))  # Иконка палитры
            # source: https://www.flaticon.com/ru/free-icon/watercolor_6651740
            color_btn.setIconSize(QSize(20, 20))
            color_btn.setFixedSize(30, 30)
            color_btn.setStyleSheet("border: none;")
            color_btn.clicked.connect(lambda _, i=idx: self.change_color(i))
            row_layout.addWidget(color_btn)

            # Кнопка редактирования
            edit_btn = QPushButton()
            edit_btn.setIcon(QIcon(os.path.join(base_dir, "images/interface/edit.png")))
            # source: https://www.flaticon.com/ru/free-icon/pen_1659764
            edit_btn.setIconSize(QSize(20, 20))
            edit_btn.setFixedSize(30, 30)
            edit_btn.setStyleSheet("border: none;")
            edit_btn.clicked.connect(lambda _, x=idx: self.edit_position(x))
            row_layout.addWidget(edit_btn)

            # Кнопка удаления
            del_btn = QPushButton()
            del_btn.setIcon(QIcon(os.path.join(base_dir, "images/interface/delete.png")))
            # source: https://www.flaticon.com/ru/free-icon/delete_709518
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
                layout.insertWidget(0, editor)
                editor.returnPressed.connect(lambda: self.save_edited_position(index, editor))
                editor.setFocus()
                break

    def save_edited_position(self, index, editor):
        new_text = editor.text().strip()
        current_text = self.positions[index]["name"]

        # Проверка: либо имя не пустое и не дублирует чужие
        if new_text and (new_text == current_text or all(
                pos["name"] != new_text for i, pos in enumerate(self.positions) if i != index)):
            self.positions[index]["name"] = new_text
            self.save_positions()
            self.refresh_list()
        else:
            QMessageBox.warning(self, "Ошибка", "Название пустое или уже существует!")

    def change_color(self, index):
        current_color = self.positions[index]["color"]
        color = QColorDialog.getColor(QColor(current_color), self, "Выберите цвет должности")
        if color.isValid():
            self.positions[index]["color"] = color.name()
            self.save_positions()
            self.refresh_list()

    def delete_position(self, index):
        del self.positions[index]
        self.save_positions()
        self.refresh_list()

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
