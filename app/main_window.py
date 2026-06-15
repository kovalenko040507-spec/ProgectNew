# app/main_window.py
from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel
from modules.currency_tracker.widget import CurrencyTrackerWidget
from modules.habit_tracker.widget import HabitTrackerWidget  # ← ДОБАВИТЬ
import sys


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperApp")

        tabs = QTabWidget()

        tabs.addTab(CurrencyTrackerWidget(), "💱 Курсы валют")
        tabs.addTab(HabitTrackerWidget(), "🎯 Трекер привычек")  # ← ДОБАВИТЬ

        for i in range(3, 6):
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.addWidget(QLabel(f"Модуль {i}: заглушка"))
            tabs.addTab(page, f"Модуль {i}")

        self.setCentralWidget(tabs)


def run_app():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())