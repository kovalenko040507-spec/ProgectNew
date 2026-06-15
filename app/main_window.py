from PyQt6.QtWidgets import QApplication,QMainWindow,QTabWidget,QWidget,QVBoxLayout,QLabel
from modules.currency_tracker.widget import CurrencyTrackerWidget
import sys

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SuperApp")

        tabs = QTabWidget()

        tabs.addTab(CurrencyTrackerWidget(), "Курсы валют")

        for i in range(2,6):
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
