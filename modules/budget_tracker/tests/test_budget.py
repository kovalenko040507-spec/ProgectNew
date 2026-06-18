# modules/budget_tracker/tests/test_budget.py
import os
import unittest

from modules.budget_tracker.models import Transaction, Category, Goal, BudgetEngine
from modules.budget_tracker.storage import BudgetStorage


class TestTransaction(unittest.TestCase):
    def test_create_transaction(self):
        t = Transaction(
            id="1",
            type="EXPENSE",
            amount=500.0,
            category="Еда",
            date="2026-06-15"
        )
        self.assertEqual(t.amount, 500.0)
        self.assertEqual(t.get_type_name(), "Расход")

    def test_to_dict_and_from_dict(self):
        t = Transaction(
            id="2",
            type="INCOME",
            amount=10000.0,
            category="Стипендия",
            date="2026-06-01",
            description="Июнь"
        )
        data = t.to_dict()
        restored = Transaction.from_dict(data)
        self.assertEqual(restored.amount, 10000.0)
        self.assertEqual(restored.description, "Июнь")


class TestGoal(unittest.TestCase):
    def test_create_goal(self):
        g = Goal(
            id="1",
            name="Ноутбук",
            target_amount=50000.0,
            current_amount=10000.0
        )
        self.assertEqual(g.get_progress_percent(), 20.0)
        self.assertFalse(g.is_completed())

    def test_completed_goal(self):
        g = Goal(
            id="2",
            name="Телефон",
            target_amount=30000.0,
            current_amount=35000.0
        )
        self.assertTrue(g.is_completed())
        self.assertEqual(g.get_progress_percent(), 100.0)


class TestBudgetEngine(unittest.TestCase):
    def setUp(self):
        self.transactions = [
            Transaction(id="1", type="INCOME", amount=15000, category="Стипендия", date="2026-06-01"),
            Transaction(id="2", type="EXPENSE", amount=500, category="Еда", date="2026-06-02"),
            Transaction(id="3", type="EXPENSE", amount=1200, category="Транспорт", date="2026-06-03"),
            Transaction(id="4", type="EXPENSE", amount=800, category="Еда", date="2026-06-10"),
        ]
        self.categories = [
            Category(id="c1", name="Еда", color="#4ade80"),
            Category(id="c2", name="Транспорт", color="#fbbf24"),
        ]
        self.goals = [
            Goal(id="g1", name="Ноутбук", target_amount=50000, current_amount=10000)
        ]
        self.engine = BudgetEngine(self.transactions, self.categories, self.goals)

    def test_balance(self):
        balance = self.engine.get_balance()
        self.assertEqual(balance, 15000 - 500 - 1200 - 800)

    def test_total_income(self):
        self.assertEqual(self.engine.get_total_income(), 15000)

    def test_total_expense(self):
        self.assertEqual(self.engine.get_total_expense(), 2500)

    def test_last_transactions(self):
        last = self.engine.get_last_transactions(2)
        self.assertEqual(len(last), 2)

    def test_expenses_by_category(self):
        expenses = self.engine.get_expenses_by_category(2026, 6)
        self.assertEqual(expenses["Еда"], 1300)
        self.assertEqual(expenses["Транспорт"], 1200)

    def test_monthly_stats(self):
        stats = self.engine.get_monthly_stats(2026, 6)
        self.assertEqual(stats["income"], 15000)
        self.assertEqual(stats["expense"], 2500)
        self.assertEqual(stats["balance"], 12500)
        self.assertEqual(stats["transaction_count"], 4)

    def test_add_income_to_goal(self):
        self.assertTrue(self.engine.add_income_to_goal("g1", 5000))
        goal = self.goals[0]
        self.assertEqual(goal.current_amount, 15000)


class TestBudgetStorage(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_budget.json"
        self.storage = BudgetStorage(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load(self):
        transactions = [
            Transaction(id="1", type="INCOME", amount=1000, category="Test", date="2026-06-01")
        ]
        categories = [Category(id="c1", name="Test", color="#fff")]
        goals = [Goal(id="g1", name="Test", target_amount=5000)]

        self.assertTrue(self.storage.save(transactions, categories, goals))

        loaded_t, loaded_c, loaded_g = self.storage.load()
        self.assertEqual(len(loaded_t), 1)
        self.assertEqual(len(loaded_c), 1)
        self.assertEqual(len(loaded_g), 1)

    def test_export_csv(self):
        transactions = [
            Transaction(id="1", type="EXPENSE", amount=500, category="Еда", date="2026-06-01")
        ]
        csv_file = "test_budget_export.csv"
        self.assertTrue(self.storage.export_to_csv(transactions, csv_file))
        self.assertTrue(os.path.exists(csv_file))
        os.remove(csv_file)


if __name__ == "__main__":
    unittest.main()