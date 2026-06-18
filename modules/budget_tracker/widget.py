# modules/budget_tracker/widget.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QComboBox, QScrollArea, QFrame,
                             QFileDialog, QMessageBox, QInputDialog, QDialog,
                             QDialogButtonBox, QFormLayout, QTableWidget,
                             QTableWidgetItem, QHeaderView, QTabWidget,
                             QDateEdit, QDoubleSpinBox)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont
from datetime import datetime, date
from typing import List, Optional, Dict
from .models import Transaction, Category, Goal, BudgetEngine, TransactionType, DefaultCategory
from .storage import BudgetStorage

# Импорты для matplotlib
try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    Figure = None
    FigureCanvas = None

import uuid


class BalanceCard(QFrame):
    """Карточка с балансом"""

    def __init__(self, balance: float, income: float, expense: float, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d44;
                border-radius: 10px;
                padding: 15px;
            }
        """)
        self._create_ui(balance, income, expense)

    def _create_ui(self, balance: float, income: float, expense: float):
        layout = QVBoxLayout(self)

        # Баланс
        balance_label = QLabel("💰 Текущий баланс")
        balance_label.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        layout.addWidget(balance_label)

        balance_value = QLabel(f"{balance:,.2f} ₽")
        balance_value.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        balance_value.setStyleSheet("color: #4a9eff;")
        layout.addWidget(balance_value)

        # Доходы и расходы
        stats_layout = QHBoxLayout()

        income_label = QLabel(f"📈 Доходы: {income:,.2f} ₽")
        income_label.setStyleSheet("color: #4ade80;")
        stats_layout.addWidget(income_label)

        expense_label = QLabel(f"📉 Расходы: {expense:,.2f} ₽")
        expense_label.setStyleSheet("color: #f87171;")
        stats_layout.addWidget(expense_label)

        layout.addLayout(stats_layout)


class TransactionRow(QFrame):
    """Строка транзакции"""

    def __init__(self, transaction: Transaction, parent=None):
        super().__init__(parent)
        self.transaction = transaction
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d44;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        self._create_ui()

    def _create_ui(self):
        layout = QHBoxLayout(self)

        # Иконка типа
        icon = QLabel("💸" if self.transaction.type == "EXPENSE" else "💰")
        icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(icon)

        # Описание и категория
        info_layout = QVBoxLayout()
        desc = self.transaction.description or self.transaction.category
        desc_label = QLabel(desc)
        desc_label.setStyleSheet("color: white; font-weight: bold;")
        info_layout.addWidget(desc_label)

        cat_label = QLabel(f"{self.transaction.category} • {self.transaction.date}")
        cat_label.setStyleSheet("color: #a0a0b0; font-size: 10px;")
        info_layout.addWidget(cat_label)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Сумма
        amount = self.transaction.amount
        color = "#f87171" if self.transaction.type == "EXPENSE" else "#4ade80"
        sign = "-" if self.transaction.type == "EXPENSE" else "+"
        amount_label = QLabel(f"{sign}{amount:,.2f} ₽")
        amount_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        layout.addWidget(amount_label)


class GoalCard(QFrame):
    """Карточка цели накопления"""

    def __init__(self, goal: Goal, parent=None):
        super().__init__(parent)
        self.goal = goal
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d44;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        # Название
        name_label = QLabel(f"🎯 {self.goal.name}")
        name_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: white;")
        layout.addWidget(name_label)

        # Прогресс
        progress = self.goal.get_progress_percent()
        progress_label = QLabel(f"{progress:.1f}% ({self.goal.current_amount:,.2f} / {self.goal.target_amount:,.2f} ₽)")
        progress_label.setStyleSheet("color: #4a9eff;")
        layout.addWidget(progress_label)

        # Прогресс-бар
        bar_frame = QFrame()
        bar_frame.setStyleSheet("background-color: #1e1e2e; border-radius: 4px;")
        bar_layout = QHBoxLayout(bar_frame)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        filled_width = int(progress / 100 * 200)
        filled = QFrame()
        filled.setStyleSheet("background-color: #4a9eff; border-radius: 4px;")
        filled.setFixedWidth(max(0, filled_width))
        filled.setFixedHeight(8)
        bar_layout.addWidget(filled)
        bar_layout.addStretch()
        layout.addWidget(bar_frame)

        # Дедлайн
        days = self.goal.get_days_remaining()
        if days >= 0:
            deadline_label = QLabel(f"Осталось дней: {days}")
            deadline_label.setStyleSheet("color: #fbbf24; font-size: 10px;")
            layout.addWidget(deadline_label)

        if self.goal.is_completed():
            completed_label = QLabel("✅ Цель достигнута!")
            completed_label.setStyleSheet("color: #4ade80; font-weight: bold;")
            layout.addWidget(completed_label)


class BudgetWidget(QWidget):
    """Главный виджет управления бюджетом"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = BudgetStorage()
        self.transactions, self.categories, self.goals = self.storage.load()
        self.engine = BudgetEngine(self.transactions, self.categories, self.goals)
        self._create_ui()
        self._refresh_display()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("💰 Управление бюджетом")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff;")
        main_layout.addWidget(title)

        # Баланс
        self.balance_card = BalanceCard(0, 0, 0)
        main_layout.addWidget(self.balance_card)

        # Панель действий
        action_layout = QHBoxLayout()

        btn_add_income = QPushButton("💰 Добавить доход")
        btn_add_income.clicked.connect(lambda: self._add_transaction("INCOME"))
        action_layout.addWidget(btn_add_income)

        btn_add_expense = QPushButton("💸 Добавить расход")
        btn_add_expense.clicked.connect(lambda: self._add_transaction("EXPENSE"))
        action_layout.addWidget(btn_add_expense)

        btn_add_goal = QPushButton("🎯 Добавить цель")
        btn_add_goal.clicked.connect(self._add_goal)
        action_layout.addWidget(btn_add_goal)

        btn_export = QPushButton("📤 Экспорт CSV")
        btn_export.clicked.connect(self._export_csv)
        action_layout.addWidget(btn_export)

        main_layout.addLayout(action_layout)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #383854;
                background-color: #1e1e2e;
            }
            QTabBar::tab {
                background-color: #2d2d44;
                color: white;
                padding: 8px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #4a9eff;
            }
        """)

        # Вкладка транзакций
        trans_widget = QWidget()
        trans_layout = QVBoxLayout(trans_widget)
        self.trans_scroll = QScrollArea()
        self.trans_scroll.setWidgetResizable(True)
        self.trans_content = QWidget()
        self.trans_layout_inner = QVBoxLayout(self.trans_content)
        self.trans_layout_inner.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.trans_scroll.setWidget(self.trans_content)
        trans_layout.addWidget(self.trans_scroll)
        self.tabs.addTab(trans_widget, "📋 Транзакции")

        # Вкладка целей
        goals_widget = QWidget()
        goals_layout = QVBoxLayout(goals_widget)
        self.goals_scroll = QScrollArea()
        self.goals_scroll.setWidgetResizable(True)
        self.goals_content = QWidget()
        self.goals_layout_inner = QVBoxLayout(self.goals_content)
        self.goals_layout_inner.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.goals_scroll.setWidget(self.goals_content)
        goals_layout.addWidget(self.goals_scroll)
        self.tabs.addTab(goals_widget, "🎯 Цели")

        # Вкладка статистики
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)

        # Выбор месяца
        month_layout = QHBoxLayout()
        month_layout.addWidget(QLabel("Месяц:"))
        self.month_select = QComboBox()
        self.month_select.addItems([
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ])
        self.month_select.setCurrentIndex(date.today().month - 1)
        self.month_select.currentIndexChanged.connect(self._update_stats)
        month_layout.addWidget(self.month_select)

        self.year_select = QComboBox()
        current_year = date.today().year
        for year in range(current_year - 2, current_year + 1):
            self.year_select.addItem(str(year))
        self.year_select.setCurrentIndex(2)
        self.year_select.currentIndexChanged.connect(self._update_stats)
        month_layout.addWidget(self.year_select)
        month_layout.addStretch()
        stats_layout.addLayout(month_layout)

        # Круговая диаграмма
        if MATPLOTLIB_AVAILABLE and FigureCanvas:
            self.figure = Figure(figsize=(6, 4), facecolor='#1e1e2e')
            self.canvas = FigureCanvas(self.figure)
            stats_layout.addWidget(self.canvas)
        else:
            no_chart_label = QLabel("📊 Matplotlib не установлен. Установите: pip install matplotlib")
            no_chart_label.setStyleSheet("color: #fbbf24; padding: 20px;")
            no_chart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_layout.addWidget(no_chart_label)
            self.figure = None
            self.canvas = None

        # Статистика месяца
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("color: white; padding: 10px;")
        stats_layout.addWidget(self.stats_label)

        self.tabs.addTab(stats_widget, "📊 Статистика")

        main_layout.addWidget(self.tabs)

    def _refresh_display(self):
        """Обновить все отображения"""
        self.engine = BudgetEngine(self.transactions, self.categories, self.goals)

        # Обновить баланс
        balance = self.engine.get_balance()
        income = self.engine.get_total_income()
        expense = self.engine.get_total_expense()

        # Пересоздать карточку баланса
        old_card = self.balance_card
        self.balance_card = BalanceCard(balance, income, expense)

        # Безопасная замена виджета
        main_layout = self.layout()
        if main_layout:
            index = main_layout.indexOf(old_card)
            if index >= 0:
                main_layout.removeWidget(old_card)
                main_layout.insertWidget(index, self.balance_card)
            old_card.deleteLater()

        # Обновить транзакции
        self._update_transactions()

        # Обновить цели
        self._update_goals()

        # Обновить статистику
        self._update_stats()

        # Сохранить
        self.storage.save(self.transactions, self.categories, self.goals)

    def _update_transactions(self):
        """Обновить список транзакций"""
        # Безопасная очистка
        while self.trans_layout_inner.count() > 0:
            item = self.trans_layout_inner.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        last_trans = self.engine.get_last_transactions(10)

        if not last_trans:
            label = QLabel("Нет транзакций. Добавьте первую!")
            label.setStyleSheet("color: #a0a0b0;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.trans_layout_inner.addWidget(label)
        else:
            for t in last_trans:
                row = TransactionRow(t)
                self.trans_layout_inner.addWidget(row)

                # Кнопка удаления
                btn_del = QPushButton("🗑️")
                btn_del.setFixedWidth(40)
                btn_del.setStyleSheet("color: #f87171;")
                btn_del.clicked.connect(lambda checked, trans=t: self._delete_transaction(trans))
                self.trans_layout_inner.addWidget(btn_del)

        self.trans_layout_inner.addStretch()

    def _update_goals(self):
        """Обновить список целей"""
        # Безопасная очистка
        while self.goals_layout_inner.count() > 0:
            item = self.goals_layout_inner.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if not self.goals:
            label = QLabel("Нет целей накоплений. Добавьте первую!")
            label.setStyleSheet("color: #a0a0b0;")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.goals_layout_inner.addWidget(label)
        else:
            for goal in self.goals:
                card = GoalCard(goal)
                self.goals_layout_inner.addWidget(card)

                # Кнопки действий
                btn_layout = QHBoxLayout()

                btn_add = QPushButton("➕ Пополнить")
                btn_add.clicked.connect(lambda checked, g=goal: self._add_to_goal(g))
                btn_layout.addWidget(btn_add)

                btn_del = QPushButton("🗑️ Удалить")
                btn_del.setStyleSheet("color: #f87171;")
                btn_del.clicked.connect(lambda checked, g=goal: self._delete_goal(g))
                btn_layout.addWidget(btn_del)

                btn_layout.addStretch()
                self.goals_layout_inner.addLayout(btn_layout)

        self.goals_layout_inner.addStretch()

    def _update_stats(self):
        """Обновить статистику и круговую диаграмму"""
        month = self.month_select.currentIndex() + 1
        year = int(self.year_select.currentText())

        stats = self.engine.get_monthly_stats(year, month)
        self.stats_label.setText(
            f"📊 {self.month_select.currentText()} {year}\n"
            f"Доходы: {stats['income']:,.2f} ₽ | "
            f"Расходы: {stats['expense']:,.2f} ₽ | "
            f"Баланс: {stats['balance']:,.2f} ₽ | "
            f"Транзакций: {stats['transaction_count']}"
        )

        # Круговая диаграмма
        if not MATPLOTLIB_AVAILABLE or self.figure is None:
            return

        expenses_by_cat = self.engine.get_expenses_by_category(year, month)

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        if not expenses_by_cat:
            ax.text(0.5, 0.5, 'Нет данных', ha='center', va='center',
                    color='white', transform=ax.transAxes)
        else:
            labels = list(expenses_by_cat.keys())
            sizes = list(expenses_by_cat.values())
            colors = []
            for cat_name in labels:
                cat = next((c for c in self.categories if c.name == cat_name), None)
                if cat is not None:
                    colors.append(cat.color)
                else:
                    colors.append('#4a9eff')

            ax.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%',
                   startangle=90, textprops={'color': 'white'})
            ax.set_title(f'Расходы за {self.month_select.currentText()} {year}',
                         color='white', pad=20)

        self.figure.set_facecolor('#1e1e2e')
        if self.canvas:
            self.canvas.draw()

    def _add_transaction(self, trans_type: str):
        """Добавить транзакцию"""
        dialog = TransactionDialog(self, trans_type, self.categories)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                transaction = Transaction(
                    id=str(uuid.uuid4()),
                    **data
                )
                self.transactions.append(transaction)
                self._refresh_display()
                QMessageBox.information(self, "Успех", "Транзакция добавлена!")

    def _delete_transaction(self, transaction: Transaction):
        """Удалить транзакцию"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить транзакцию '{transaction.description or transaction.category}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if transaction in self.transactions:
                self.transactions.remove(transaction)
                self._refresh_display()

    def _add_goal(self):
        """Добавить цель"""
        dialog = GoalDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if data:
                goal = Goal(
                    id=str(uuid.uuid4()),
                    **data
                )
                self.goals.append(goal)
                self._refresh_display()
                QMessageBox.information(self, "Успех", "Цель добавлена!")

    def _add_to_goal(self, goal: Goal):
        """Пополнить цель"""
        amount, ok = QInputDialog.getDouble(
            self, "Пополнить цель",
            f"Сумма для цели '{goal.name}':",
            0, 0, 1000000, 2
        )
        if ok and amount > 0:
            self.engine.add_income_to_goal(goal.id, amount)
            self._refresh_display()
            QMessageBox.information(self, "Успех", f"Добавлено {amount:,.2f} ₽ к цели!")

    def _delete_goal(self, goal: Goal):
        """Удалить цель"""
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить цель '{goal.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if goal in self.goals:
                self.goals.remove(goal)
                self._refresh_display()

    def _export_csv(self):
        """Экспорт в CSV"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в CSV", "budget_export.csv", "CSV Files (*.csv)"
        )
        if filepath:
            if self.storage.export_to_csv(self.transactions, filepath):
                QMessageBox.information(self, "Успех", f"Экспортировано в {filepath}")


class TransactionDialog(QDialog):
    """Диалог добавления транзакции"""

    def __init__(self, parent=None, trans_type: str = "EXPENSE", categories: Optional[List] = None):
        super().__init__(parent)
        self.trans_type = trans_type
        self.categories = categories or []
        self.setWindowTitle("💰 Доход" if trans_type == "INCOME" else "💸 Расход")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #1e1e2e;")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Сумма
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setValue(0)
        self.amount_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Сумма (₽):", self.amount_input)

        # Категория
        self.category_combo = QComboBox()
        if self.categories:
            self.category_combo.addItems([c.name for c in self.categories])
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Категория:", self.category_combo)

        # Дата
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setCalendarPopup(True)
        self.date_input.setStyleSheet("""
            QDateEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Дата:", self.date_input)

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
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> Optional[Dict]:
        amount = self.amount_input.value()
        if amount <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма должна быть больше 0")
            return None

        return {
            "type": self.trans_type,
            "amount": amount,
            "category": self.category_combo.currentText(),
            "date": self.date_input.date().toString("yyyy-MM-dd"),
            "description": self.desc_input.text()
        }


class GoalDialog(QDialog):
    """Диалог добавления цели"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎯 Новая цель накопления")
        self.resize(400, 300)
        self.setStyleSheet("background-color: #1e1e2e;")
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Название
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Название цели")
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

        # Целевая сумма
        self.target_input = QDoubleSpinBox()
        self.target_input.setRange(0, 10000000)
        self.target_input.setDecimals(2)
        self.target_input.setValue(10000)
        self.target_input.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Целевая сумма (₽):", self.target_input)

        # Дедлайн
        self.deadline_input = QDateEdit()
        self.deadline_input.setDate(QDate.currentDate().addMonths(6))
        self.deadline_input.setCalendarPopup(True)
        self.deadline_input.setStyleSheet("""
            QDateEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        form.addRow("Дедлайн:", self.deadline_input)

        layout.addLayout(form)

        # Кнопки
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> Optional[Dict]:
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Ошибка", "Введите название цели")
            return None

        target = self.target_input.value()
        if target <= 0:
            QMessageBox.warning(self, "Ошибка", "Целевая сумма должна быть больше 0")
            return None

        return {
            "name": name,
            "target_amount": target,
            "deadline": self.deadline_input.date().toString("yyyy-MM-dd")
        }