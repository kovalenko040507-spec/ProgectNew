# modules/budget_tracker/storage.py
import json
from pathlib import Path
from typing import List
from .models import Transaction, Category, Goal, DefaultCategory


def _get_default_categories() -> List[Category]:
    """Получить категории по умолчанию"""
    colors = ["#4ade80", "#fbbf24", "#f87171", "#60a5fa", "#a78bfa", "#fb923c", "#2dd4bf", "#94a3b8"]
    categories = []
    for i, cat in enumerate(DefaultCategory):
        categories.append(Category(
            id=str(uuid.uuid4()),
            name=cat.value,
            color=colors[i % len(colors)],
            is_default=True
        ))
    return categories


def export_to_csv(transactions: List[Transaction], filepath: str) -> bool:
    """Экспорт транзакций в CSV"""
    try:
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Тип", "Сумма", "Категория", "Дата", "Описание"])
            for t in sorted(transactions, key=lambda x: x.date):
                writer.writerow([
                    t.get_type_name(),
                    t.amount,
                    t.category,
                    t.date,
                    t.description
                ])
        return True
    except (IOError, OSError) as e:
        print(f"Ошибка экспорта: {e}")
        return False


class BudgetStorage:
    """Хранение данных бюджета в JSON"""

    def __init__(self, filepath: str = "budget_data.json"):
        self.filepath = Path(filepath)

    def save(self, transactions: List[Transaction], categories: List[Category], goals: List[Goal]) -> bool:
        """Сохранить все данные"""
        try:
            data = {
                "transactions": [t.to_dict() for t in transactions],
                "categories": [c.to_dict() for c in categories],
                "goals": [g.to_dict() for g in goals]
            }
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError, json.JSONEncodeError) as e:
            print(f"Ошибка сохранения бюджета: {e}")
            return False

    def load(self) -> tuple:
        """Загрузить все данные"""
        if not self.filepath.exists():
            return [], _get_default_categories(), []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            transactions = [Transaction.from_dict(t) for t in data.get("transactions", [])]
            categories = [Category.from_dict(c) for c in data.get("categories", [])]
            goals = [Goal.from_dict(g) for g in data.get("goals", [])]

            return transactions, categories, goals
        except (IOError, OSError, json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка загрузки бюджета: {e}")
            return [], _get_default_categories(), []


import uuid