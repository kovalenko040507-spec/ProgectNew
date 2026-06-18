# modules/schedule/widget.py
from datetime import datetime

import pyqtgraph as pg
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QComboBox, QLineEdit, QFormLayout,
                             QScrollArea, QFrame, QMessageBox,
                             QTimeEdit, QDialog, QDialogButtonBox,
                             QTableWidget, QTableWidgetItem, QHeaderView)

from .models import Lesson, ScheduleEngine, DayOfWeek, LessonType
from .storage import ScheduleStorage


class LessonCard(QFrame):
    """Карточка занятия"""

    def __init__(self, lesson: Lesson, parent=None):
        super().__init__(parent)
        self.lesson = lesson
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d44;
                border-radius: 8px;
                padding: 10px;
                border-left: 4px solid #4a9eff;
            }
        """)
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()
        title = QLabel(self.lesson.name)
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header.addWidget(title)

        # Тип занятия
        type_label = QLabel(self.lesson.get_type_name())
        type_label.setStyleSheet("color: #fbbf24; font-size: 10px;")
        header.addWidget(type_label)
        header.addStretch()
        layout.addLayout(header)

        # Время и аудитория
        time_str = f"⏰ {self.lesson.start_time} - {self.lesson.end_time}"
        if self.lesson.classroom:
            time_str += f" | 📍 {self.lesson.classroom}"

        time_label = QLabel(time_str)
        time_label.setStyleSheet("color: #a0a0b0;")
        layout.addWidget(time_label)

        # Длительность
        duration_label = QLabel(f"⏱️ {self.lesson.get_duration_minutes()} мин.")
        duration_label.setStyleSheet("color: #4ade80; font-size: 10px;")
        layout.addWidget(duration_label)

        # Статус
        status_label = QLabel(f"Статус: {self.lesson.get_status_name()}")
        status_label.setStyleSheet("color: #a0a0b0; font-size: 10px;")
        layout.addWidget(status_label)


class ScheduleWidget(QWidget):
    """Главный виджет расписания"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = ScheduleStorage()
        self.lessons = self.storage.load()
        self.engine = ScheduleEngine(self.lessons)

        # Таймер для обновления обратного отсчёта
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_countdown)
        self.timer.start(1000)  # Обновление каждую секунду

        self._create_ui()
        self._refresh_display()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("📅 Расписание занятий")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff;")
        main_layout.addWidget(title)

        # Панель управления
        control_layout = QHBoxLayout()

        btn_add = QPushButton("➕ Добавить занятие")
        btn_add.clicked.connect(self._add_lesson)
        control_layout.addWidget(btn_add)

        btn_day = QComboBox()
        btn_day.addItems([day.get_name_ru() for day in DayOfWeek])
        btn_day.currentIndexChanged.connect(self._show_day_schedule)
        control_layout.addWidget(btn_day)

        control_layout.addStretch()
        main_layout.addLayout(control_layout)

        # Обратный отсчёт
        self.countdown_label = QLabel("⏳ Загрузка...")
        self.countdown_label.setFont(QFont("Arial", 12))
        self.countdown_label.setStyleSheet(
            "color: #fbbf24; background-color: #2d2d44; padding: 10px; border-radius: 5px;")
        main_layout.addWidget(self.countdown_label)

        # Вкладки: Сетка недели / Список
        tabs_layout = QHBoxLayout()

        btn_week_view = QPushButton("📊 Неделя")
        btn_week_view.clicked.connect(self._show_week_view)
        tabs_layout.addWidget(btn_week_view)

        btn_list_view = QPushButton("📋 Список")
        btn_list_view.clicked.connect(self._show_list_view)
        tabs_layout.addWidget(btn_list_view)

        btn_stats = QPushButton("📈 Статистика")
        btn_stats.clicked.connect(self._show_stats)
        tabs_layout.addWidget(btn_stats)

        tabs_layout.addStretch()
        main_layout.addLayout(tabs_layout)

        # Область отображения
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.content_widget)
        main_layout.addWidget(self.scroll)

    def _refresh_display(self):
        """Обновить отображение"""
        self.engine = ScheduleEngine(self.lessons)
        self._update_countdown()
        self._show_week_view()

    def _update_countdown(self):
        """Обновить обратный отсчёт до следующего занятия"""
        next_lesson = self.engine.get_next_lesson()

        if next_lesson:
            time_until = self.engine.get_time_until_next_lesson(next_lesson)

            days = time_until.days
            hours = time_until.seconds // 3600
            minutes = (time_until.seconds % 3600) // 60
            seconds = time_until.seconds % 60

            if days > 0:
                text = f"⏳ До '{next_lesson.name}': {days} дн. {hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                text = f"⏳ До '{next_lesson.name}': {hours:02d}:{minutes:02d}:{seconds:02d}"

            self.countdown_label.setText(text)
        else:
            self.countdown_label.setText("✅ Занятий на эту неделю нет")

    def _show_week_view(self):
        """Показать сетку недели"""
        self._clear_content()

        for day in DayOfWeek:
            day_layout = QVBoxLayout()

            day_title = QLabel(f"📌 {day.get_name_ru()}")
            day_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            day_title.setStyleSheet("color: #4a9eff;")
            day_layout.addWidget(day_title)

            day_lessons = self.engine.get_lessons_for_day(day)

            if not day_lessons:
                empty_label = QLabel("  Нет занятий")
                empty_label.setStyleSheet("color: #666;")
                day_layout.addWidget(empty_label)
            else:
                for lesson in day_lessons:
                    card = LessonCard(lesson)
                    day_layout.addWidget(card)

            day_frame = QFrame()
            day_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 5px; padding: 10px;")
            day_frame.setLayout(day_layout)
            self.content_layout.addWidget(day_frame)

        self.content_layout.addStretch()

    def _show_list_view(self):
        """Показать список всех занятий"""
        self._clear_content()

        if not self.lessons:
            label = QLabel("Расписание пусто. Добавьте занятия!")
            label.setStyleSheet("color: #a0a0b0;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(label)
        else:
            for lesson in sorted(self.lessons, key=lambda x: (x.day_of_week, x.start_time)):
                card = LessonCard(lesson)
                self.content_layout.addWidget(card)

                # Кнопки редактирования/удаления
                btn_layout = QHBoxLayout()

                btn_edit = QPushButton("✏️ Редактировать")
                btn_edit.clicked.connect(lambda checked, l=lesson: self._edit_lesson(l))
                btn_layout.addWidget(btn_edit)

                btn_delete = QPushButton("🗑️ Удалить")
                btn_delete.setStyleSheet("color: #f87171;")
                btn_delete.clicked.connect(lambda checked, l=lesson: self._delete_lesson(l))
                btn_layout.addWidget(btn_delete)

                btn_layout.addStretch()
                self.content_layout.addLayout(btn_layout)

        self.content_layout.addStretch()

    def _show_day_schedule(self, day_index: int):
        """Показать расписание на конкретный день"""
        self._clear_content()

        day = DayOfWeek(day_index)
        title = QLabel(f"📌 {day.get_name_ru()}")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff;")
        self.content_layout.addWidget(title)

        lessons = self.engine.get_lessons_for_day(day)

        if not lessons:
            label = QLabel("Нет занятий")
            label.setStyleSheet("color: #a0a0b0;")
            self.content_layout.addWidget(label)
        else:
            for lesson in lessons:
                card = LessonCard(lesson)
                self.content_layout.addWidget(card)

        self.content_layout.addStretch()

    def _show_stats(self):
        """Показать статистику нагрузки"""
        dialog = QDialog(self)
        dialog.setWindowTitle("📊 Статистика учебной нагрузки")
        dialog.resize(800, 600)
        dialog.setStyleSheet("background-color: #1e1e2e;")

        layout = QVBoxLayout(dialog)

        # Общая статистика
        total_hours = self.engine.get_total_weekly_hours()
        total_label = QLabel(f"📚 Всего часов в неделю: {total_hours}")
        total_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        total_label.setStyleSheet("color: white;")
        layout.addWidget(total_label)

        # График
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('#2d2d44')

        load = self.engine.get_weekly_load()
        days = list(load.keys())
        hours = [load[day]["total_hours"] for day in days]

        plot_widget.plot(
            range(len(days)),
            hours,
            pen=pg.mkPen('#4a9eff', width=2),
            symbol='o',
            symbolBrush='#4a9eff',
            symbolSize=10
        )
        plot_widget.setLabel('left', 'Часов')
        plot_widget.setLabel('bottom', 'День недели')
        plot_widget.getAxis('bottom').setTicks([list(enumerate(days))])
        plot_widget.showGrid(x=True, y=True, alpha=0.3)

        layout.addWidget(plot_widget)

        # Таблица
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["День", "Занятий", "Часов"])
        table.setRowCount(len(days))

        for i, day in enumerate(days):
            table.setItem(i, 0, QTableWidgetItem(day))
            table.setItem(i, 1, QTableWidgetItem(str(load[day]["lessons_count"])))
            table.setItem(i, 2, QTableWidgetItem(str(load[day]["total_hours"])))

        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        table.setStyleSheet("background-color: #2d2d44; color: white;")

        layout.addWidget(table)

        dialog.exec()

    def _add_lesson(self):
        """Добавить занятие"""
        dialog = LessonDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            lesson_data = dialog.get_lesson_data()
            lesson = Lesson(
                id=str(__import__('uuid').uuid4()),
                **lesson_data
            )

            if self.storage.add_lesson(self.lessons, lesson):
                self._refresh_display()
                QMessageBox.information(self, "Успех", "Занятие добавлено!")
            else:
                QMessageBox.warning(self, "Ошибка", "Обнаружено пересечение по времени!")

    def _edit_lesson(self, lesson: Lesson):
        """Редактировать занятие"""
        dialog = LessonDialog(self, lesson)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            lesson_data = dialog.get_lesson_data()
            updated_lesson = Lesson(id=lesson.id, **lesson_data)

            if self.storage.update_lesson(self.lessons, lesson.id, updated_lesson):
                self._refresh_display()
                QMessageBox.information(self, "Успех", "Занятие обновлено!")
            else:
                QMessageBox.warning(self, "Ошибка", "Обнаружено пересечение по времени!")

    def _delete_lesson(self, lesson: Lesson):
        """Удалить занятие"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить занятие '{lesson.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.storage.delete_lesson(self.lessons, lesson.id):
                self._refresh_display()
                QMessageBox.information(self, "Успех", "Занятие удалено!")

    def _clear_content(self):
        """Очистить контент"""
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


class LessonDialog(QDialog):
    """Диалог добавления/редактирования занятия"""

    def __init__(self, parent=None, lesson: Lesson = None):
        super().__init__(parent)
        self.lesson = lesson
        self.setWindowTitle("✏️ Редактирование занятия" if lesson else "➕ Добавление занятия")
        self.resize(400, 400)
        self.setStyleSheet("background-color: #1e1e2e;")

        self._create_ui()

        if lesson:
            self._fill_data(lesson)

    def _create_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Название
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название занятия")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Название:", self.name_input)

        # День недели
        self.day_combo = QComboBox()
        self.day_combo.addItems([day.get_name_ru() for day in DayOfWeek])
        self.day_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("День недели:", self.day_combo)

        # Время начала
        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime(9, 0))
        self.start_time.setStyleSheet("""
            QTimeEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Начало:", self.start_time)

        # Время окончания
        self.end_time = QTimeEdit()
        self.end_time.setTime(QTime(10, 30))
        self.end_time.setStyleSheet("""
            QTimeEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Окончание:", self.end_time)

        # Тип занятия
        self.type_combo = QComboBox()
        self.type_combo.addItems([t.value for t in LessonType])
        self.type_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Тип:", self.type_combo)

        # Аудитория
        self.classroom_input = QLineEdit()
        self.classroom_input.setPlaceholderText("Аудитория")
        self.classroom_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Аудитория:", self.classroom_input)

        # Описание
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Описание (необязательно)")
        self.desc_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Описание:", self.desc_input)

        layout.addLayout(form)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _fill_data(self, lesson: Lesson):
        """Заполнить данными существующего занятия"""
        self.name_input.setText(lesson.name)
        self.day_combo.setCurrentIndex(lesson.day_of_week)
        start = datetime.strptime(lesson.start_time, "%H:%M")
        self.start_time.setTime(QTime(start.hour, start.minute))
        end = datetime.strptime(lesson.end_time, "%H:%M")
        self.end_time.setTime(QTime(end.hour, end.minute))

        type_index = self.type_combo.findText(lesson.get_type_name())
        if type_index >= 0:
            self.type_combo.setCurrentIndex(type_index)

        self.classroom_input.setText(lesson.classroom)
        self.desc_input.setText(lesson.description)

    def get_lesson_data(self) -> dict:
        """Получить данные занятия"""
        # Преобразуем тип занятия в enum key
        type_text = self.type_combo.currentText()
        type_key = next((k for k, v in LessonType.__members__.items() if v.value == type_text), "LECTURE")

        return {
            "name": self.name_input.text(),
            "day_of_week": self.day_combo.currentIndex(),
            "start_time": self.start_time.time().toString("HH:mm"),
            "end_time": self.end_time.time().toString("HH:mm"),
            "lesson_type": type_key,
            "classroom": self.classroom_input.text(),
            "description": self.desc_input.text(),
            "status": "SCHEDULED"
        }


