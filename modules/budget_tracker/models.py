# modules/budget_tracker/models.py
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
from typing import List


class TransactionType(Enum):
    INCOME = "Доход"
    EXPENSE = "Расход"


class DefaultCategory(Enum):
    FOOD = "Еда"
    TRANSPORT = "Транспорт"
    ENTERTAINMENT = "Развлечения"
    STUDY = "Учёба"
    HEALTH = "Здоровье"
    SHOPPING = "Покупки"
    BILLS = "Счета"
    OTHER = "Другое"


@dataclass
class Transaction:
    """Модель транзакции"""
    id: str
    type: str  # "INCOME" или "EXPENSE"
    amount: float
    category: str
    date: str  # формат YYYY-MM-DD
    description: str = ""
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_type_name(self) -> str:
        try:
            return TransactionType[self.type].value
        except KeyError:
            return self.type

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "amount": self.amount,
            "category": self.category,
            "date": self.date,
            "description": self.description,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transaction":
        return cls(**data)


@dataclass
class Category:
    """Модель категории"""
    id: str
    name: str
    color: str = "#4a9eff"
    is_default: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "is_default": self.is_default
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(**data)


@dataclass
class Goal:
    """Модель цели накопления"""
    id: str
    name: str
    target_amount: float
    current_amount: float = 0.0
    deadline: str = ""  # формат YYYY-MM-DD
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")

    def get_progress_percent(self) -> float:
        if self.target_amount <= 0:
            return 0
        return min(100.0, (self.current_amount / self.target_amount) * 100)

    def is_completed(self) -> bool:
        return self.current_amount >= self.target_amount

    def get_days_remaining(self) -> int:
        if not self.deadline:
            return -1
        try:
            deadline_date = datetime.strptime(self.deadline, "%Y-%m-%d").date()
            delta = deadline_date - date.today()
            return delta.days
        except ValueError:
            return -1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "target_amount": self.target_amount,
            "current_amount": self.current_amount,
            "deadline": self.deadline,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Goal":
        return cls(**data)


class BudgetEngine:
    """Движок управления бюджетом"""

    def __init__(self, transactions: List[Transaction], categories: List[Category], goals: List[Goal]):
        self.transactions = transactions
        self.categories = categories
        self.goals = goals

    def get_balance(self) -> float:
        """Текущий баланс"""
        income = sum(t.amount for t in self.transactions if t.type == "INCOME")
        expense = sum(t.amount for t in self.transactions if t.type == "EXPENSE")
        return income - expense

    def get_total_income(self) -> float:
        return sum(t.amount for t in self.transactions if t.type == "INCOME")

    def get_total_expense(self) -> float:
        return sum(t.amount for t in self.transactions if t.type == "EXPENSE")

    def get_last_transactions(self, count: int = 10) -> List[Transaction]:
        """Последние N транзакций"""
        sorted_trans = sorted(
            self.transactions,
            key=lambda t: t.created_at,
            reverse=True
        )
        return sorted_trans[:count]

    def get_expenses_by_category(self, year: Optional[int] = None, month: Optional[int] = None) -> dict:
        """Расходы по категориям за период"""
        result = {}

        for t in self.transactions:
            if t.type != "EXPENSE":
                continue

            trans_date = datetime.strptime(t.date, "%Y-%m-%d")

            if year and trans_date.year != year:
                continue
            if month and trans_date.month != month:
                continue

            if t.category not in result:
                result[t.category] = 0.0
            result[t.category] += t.amount

        return result

    def get_monthly_stats(self, year: int, month: int) -> dict:
        """Статистика за месяц"""
        month_transactions = [
            t for t in self.transactions
            if datetime.strptime(t.date, "%Y-%m-%d").year == year
               and datetime.strptime(t.date, "%Y-%m-%d").month == month
        ]

        income = sum(t.amount for t in month_transactions if t.type == "INCOME")
        expense = sum(t.amount for t in month_transactions if t.type == "EXPENSE")

        return {
            "income": income,
            "expense": expense,
            "balance": income - expense,
            "transaction_count": len(month_transactions)
        }

    def add_income_to_goal(self, goal_id: str, amount: float) -> bool:
        """Добавить сумму к цели"""
        for goal in self.goals:
            if goal.id == goal_id:
                goal.current_amount += amount
                return True
        return False


from typing import Optional