import os
import sys
import json

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QFrame, QLineEdit, QMessageBox, QScrollArea, QColorDialog
)
from PySide6.QtGui import QPixmap, QIcon, QColor
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QSettings, QSize, QEasingCurve

base_dir = os.path.dirname(os.path.abspath(__file__))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DelegTa")
        self.setWindowIcon(QIcon(os.path.join(base_dir, "images/interface/icon.png")))

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
        self.settings_btn.raise_()  # Поверх фона

        # --- Основной контент ---
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Основная область с панелями
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_layout.setSpacing(0)

        # Левая панель участников
        self.members_panel = QFrame()
        self.members_panel.setFixedWidth(250)
        self.members_panel.setStyleSheet("""
            background-color: rgb(30, 30, 30);
            border: none;
            color: white;
        """)
        members_layout = QVBoxLayout()
        members_layout.setContentsMargins(15, 15, 15, 15)

        # Верхняя строка: Заголовок + "+"
        header_layout = QHBoxLayout()
        title_label = QLabel("Участники")
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        header_layout.addWidget(title_label)

        btn_add = os.path.join(base_dir, "images/interface/add.png")
        # source: https://www.flaticon.com/ru/free-icon/add_3363871
        self.add_member_overlay = AddMemberOverlay(self)

        # Панель редактирования должностей
        self.edit_positions_overlay = EditPositionsOverlay(self)

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
        members_layout.addStretch()
        self.members_panel.setLayout(members_layout)
        content_layout.addWidget(self.members_panel)

        # Правая часть с задачами
        tasks_container = QVBoxLayout()
        tasks_container.setContentsMargins(15, 40, 15, 15)

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
            vbox.setSpacing(0)

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
            vbox.addStretch()  # для будущих задач
            panel.setLayout(vbox)
            tasks_row.addWidget(panel)
            self.columns.append(panel)

        tasks_container.addLayout(tasks_row)
        content_layout.addLayout(tasks_container)

        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

        # --- Панель настроек ---
        self.settings_panel = SettingsPanel(
            self,
            on_close=self.toggle_settings_panel,
            on_change_background=self.change_background,
            on_edit_positions=self.edit_positions_overlay.show_overlay
        )
        self.settings_panel.setGeometry(self.width(), 0, 300, self.height())
        self.panel_visible = False

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


class AddMemberOverlay(QFrame):
    def __init__(self, parent=None, on_close=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 150);")
        self.setVisible(False)  # скрыто по умолчанию

        self.on_close = on_close  # callback для уведомления

        # Основной лейаут (центрируем содержимое)
        overlay_layout = QVBoxLayout(self)
        overlay_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Центральная панель
        self.popup_panel = QFrame()
        self.popup_panel.setFixedSize(800, 600)
        self.popup_panel.setObjectName("addPeoplePanel")
        self.popup_panel.setStyleSheet("""
            QFrame#addPeoplePanel {
                background-color: black;
                border: 2px solid white;
                border-radius: 15px;
            }
        """)
        popup_layout = QVBoxLayout(self.popup_panel)
        popup_layout.setContentsMargins(15, 15, 15, 15)

        # Верхняя панель с крестиком
        top_bar = QHBoxLayout()
        top_bar.addStretch()
        close_btn = QPushButton("✖")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("border: none; font-size: 18px; color: white;")
        close_btn.clicked.connect(self.close_overlay)
        top_bar.addWidget(close_btn)

        popup_layout.addLayout(top_bar)

        # Заголовок
        title = QLabel("Добавить участника")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        popup_layout.addWidget(title)
        popup_layout.addStretch()

        overlay_layout.addWidget(self.popup_panel)

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
