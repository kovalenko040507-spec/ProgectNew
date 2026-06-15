# modules/habit_tracker/widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QScrollArea, QFrame,
                             QFileDialog, QMessageBox, QInputDialog, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from datetime import datetime, date, timedelta
from .models import Habit
from .storage import HabitStorage


class HabitCard(QFrame):
    """Карточка одной привычки"""

    def __init__(self, habit: Habit, parent=None):
        super().__init__(parent)
        self.habit = habit
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #2d2d44;
                border-radius: 8px;
                padding: 10px;
                border-left: 4px solid {habit.color};
            }}
        """)
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        header = QHBoxLayout()
        title = QLabel(self.habit.name)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        header.addWidget(title)

        stats = self.habit.get_stats()
        streak_label = QLabel(f"🔥 {stats['current_streak']} дн.")
        streak_label.setStyleSheet("color: #fbbf24; font-weight: bold;")
        header.addWidget(streak_label)
        header.addStretch()
        layout.addLayout(header)

        # Кнопки действий на сегодня
        today = date.today().strftime("%Y-%m-%d")
        current_status = self.habit.get_status_for_date(today)

        btn_layout = QHBoxLayout()

        self.btn_done = QPushButton("✅ Выполнено")
        self.btn_done.setEnabled(current_status is None)
        self.btn_done.clicked.connect(lambda: self._mark("done"))
        btn_layout.addWidget(self.btn_done)

        self.btn_skip = QPushButton("⏭️ Пропустить")
        self.btn_skip.setEnabled(current_status is None)
        self.btn_skip.clicked.connect(lambda: self._mark("skipped"))
        btn_layout.addWidget(self.btn_skip)

        layout.addLayout(btn_layout)

        # Статус сегодня
        if current_status:
            status_text = {
                "done": "✅ Сегодня выполнено",
                "skipped": "⏭️ Сегодня пропущено",
                "missed": "❌ Пропущено"
            }.get(current_status, "")
            status_label = QLabel(status_text)
            status_label.setStyleSheet("color: #a0a0b0;")
            layout.addWidget(status_label)

        # Статистика
        stats_text = (f"Всего: {stats['total_days']} | "
                      f"Выполнено: {stats['done']} | "
                      f"Лучшая серия: {stats['best_streak']} дн. | "
                      f"Успешность: {stats['completion_rate']}%")
        stats_label = QLabel(stats_text)
        stats_label.setStyleSheet("color: #a0a0b0; font-size: 10px;")
        layout.addWidget(stats_label)

    def _mark(self, status: str):
        today = date.today().strftime("%Y-%m-%d")
        if self.habit.mark_date(today, status):
            self._refresh()

    def _refresh(self):
        """Обновить карточку."""
        if hasattr(self.parent(), 'refresh_habits'):
            self.parent().refresh_habits()


class HabitTrackerWidget(QWidget):
    """Главный виджет трекера привычек"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = HabitStorage()
        self.habits = self.storage.load()
        self._create_ui()
        self.refresh_habits()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("🎯 Трекер привычек")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff;")
        main_layout.addWidget(title)

        # Панель добавления
        add_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название новой привычки...")
        self.name_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        add_layout.addWidget(self.name_input)

        btn_add = QPushButton("➕ Добавить")
        btn_add.clicked.connect(self._add_habit)
        add_layout.addWidget(btn_add)

        main_layout.addLayout(add_layout)

        # Панель действий
        action_layout = QHBoxLayout()

        btn_export = QPushButton("📤 Экспорт CSV")
        btn_export.clicked.connect(self._export_csv)
        action_layout.addWidget(btn_export)

        btn_import = QPushButton("📥 Импорт CSV")
        btn_import.clicked.connect(self._import_csv)
        action_layout.addWidget(btn_import)

        btn_chart = QPushButton("📊 График серий")
        btn_chart.clicked.connect(self._show_chart)
        action_layout.addWidget(btn_chart)

        action_layout.addStretch()
        main_layout.addLayout(action_layout)

        # Список привычек
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_widget)
        main_layout.addWidget(self.scroll)

    def refresh_habits(self):
        """Обновить отображение привычек."""
        # Очистить список
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.habits:
            empty_label = QLabel("Нет привычек. Добавьте первую!")
            empty_label.setStyleSheet("color: #a0a0b0;")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.scroll_layout.addWidget(empty_label)
        else:
            for habit in self.habits:
                card = HabitCard(habit, self.scroll_widget)
                self.scroll_layout.addWidget(card)

                # Кнопка удаления
                btn_del = QPushButton("🗑️ Удалить")
                btn_del.setStyleSheet("color: #f87171;")
                btn_del.clicked.connect(lambda checked, h=habit: self._delete_habit(h))
                self.scroll_layout.addWidget(btn_del)

        self.scroll_layout.addStretch()
        self.storage.save(self.habits)

    def _add_habit(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название привычки")
            return

        habit = Habit(
            id=str(uuid.uuid4()),
            name=name
        )
        self.habits.append(habit)
        self.name_input.clear()
        self.refresh_habits()

    def _delete_habit(self, habit: Habit):
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить привычку '{habit.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.habits.remove(habit)
            self.refresh_habits()

    def _export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в CSV", "habits_export.csv", "CSV Files (*.csv)"
        )
        if filepath:
            if self.storage.export_to_csv(self.habits, filepath):
                QMessageBox.information(self, "Успех", f"Экспортировано в {filepath}")

    def _import_csv(self):
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Импорт из CSV", "", "CSV Files (*.csv)"
        )
        if filepath:
            imported = self.storage.import_from_csv(filepath)
            if imported:
                self.habits.extend(imported)
                self.refresh_habits()
                QMessageBox.information(self, "Успех", f"Импортировано {len(imported)} привычек")

    def _show_chart(self):
        """Показать график серий для выбранной привычки."""
        if not self.habits:
            QMessageBox.warning(self, "Внимание", "Нет привычек для отображения")
            return

        names = [h.name for h in self.habits]
        name, ok = QInputDialog.getItem(self, "Выбор привычки", "Выберите:", names)
        if not ok or not name:
            return

        habit = next((h for h in self.habits if h.name == name), None)
        if not habit:
            return

        # Построить график серий по дням
        dates = []
        streaks = []
        current_streak = 0

        start_date = datetime.strptime(habit.created_at, "%Y-%m-%d").date()
        end_date = date.today()

        check_date = start_date
        while check_date <= end_date:
            date_str = check_date.strftime("%Y-%m-%d")
            status = habit.records.get(date_str)

            if status == "done":
                current_streak += 1
            else:
                current_streak = 0

            dates.append(check_date)
            streaks.append(current_streak)
            check_date += timedelta(days=1)

        # Показать в новом окне
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Серии: {habit.name}")
        dialog.resize(800, 400)
        dialog.setStyleSheet("background-color: #1e1e2e;")

        layout = QVBoxLayout(dialog)
        plot_widget = pg.PlotWidget()
        plot_widget.setBackground('#2d2d44')
        plot_widget.plot(
            [d.toordinal() for d in dates],
            streaks,
            pen=pg.mkPen(habit.color, width=2),
            fillLevel=0,
            brush=pg.mkBrush(habit.color + '40')
        )
        plot_widget.setLabel('left', 'Дней подряд')
        plot_widget.setLabel('bottom', 'Дата')
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(plot_widget)

        stats = habit.get_stats()
        info = QLabel(
            f"Текущая серия: {stats['current_streak']} дн. | "
            f"Лучшая серия: {stats['best_streak']} дн. | "
            f"Успешность: {stats['completion_rate']}%"
        )
        info.setStyleSheet("color: white; padding: 10px;")
        layout.addWidget(info)

        dialog.exec()


# Импортируем uuid в начале файла
import uuid
