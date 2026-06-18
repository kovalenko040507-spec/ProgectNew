# app/main_window.py
import sys

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget

from modules.budget_tracker.widget import BudgetWidget
from modules.currency_tracker.widget import CurrencyTrackerWidget
from modules.habit_tracker.widget import HabitTrackerWidget
from modules.notes_app.widget import NotesWidget
from modules.schedule.widget import ScheduleWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperApp")

        tabs = QTabWidget()

        tabs.addTab(CurrencyTrackerWidget(), " Курсы валют")
        tabs.addTab(HabitTrackerWidget(), "🎯 Трекер привычек")
        tabs.addTab(ScheduleWidget(), "📅 Расписание")
        tabs.addTab(BudgetWidget(), " Бюджет")
        tabs.addTab(NotesWidget(), "📓 Заметки")

        self.setCentralWidget(tabs)


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1400, 900)
    window.show()
    sys.exit(app.exec())