from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QComboBox, QLabel
import pyqtgraph as pg
import requests


class CurrencyTrackerWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.info = QLabel("Получение курса ЦБ РФ")
        layout.addWidget(self.info)

        self.combo = QComboBox()
        self.combo.addItems(["USD", "EUR", "CNY"])
        layout.addWidget(self.combo)

        btn = QPushButton("Загрузить")
        btn.clicked.connect(self.load_rate)
        layout.addWidget(btn)

        self.graph = pg.PlotWidget()
        layout.addWidget(self.graph)

    def load_rate(self):
        try:
            data = requests.get("https://www.cbr-xml-daily.ru/daily_json.js", timeout=10).json()
            code = self.combo.currentText()
            value = data["Valute"][code]["Value"]
            self.info.setText(f"{code}: {value} RUB")

            self.graph.clear()
            self.graph.plot([1, 2, 3, 4, 5], [value * 0.97, value * 0.99, value, value * 1.01, value * 1.03])
        except Exception as e:
            self.info.setText(str(e))