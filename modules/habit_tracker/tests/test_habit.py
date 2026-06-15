# modules/habit_tracker/tests/test_habit.py
import unittest
import os
import json
from datetime import date, timedelta
from modules.habit_tracker.models import Habit
from modules.habit_tracker.storage import HabitStorage


class TestHabit(unittest.TestCase):
    def setUp(self):
        self.habit = Habit(
            id="test-1",
            name="Бег",
            created_at=(date.today() - timedelta(days=10)).strftime("%Y-%m-%d")
        )

    def test_create_habit(self):
        self.assertEqual(self.habit.name, "Бег")
        self.assertIsNotNone(self.habit.id)

    def test_mark_date(self):
        today = date.today().strftime("%Y-%m-%d")
        self.assertTrue(self.habit.mark_date(today, "done"))
        self.assertFalse(self.habit.mark_date(today, "skipped"))
        self.assertEqual(self.habit.get_status_for_date(today), "done")

    def test_current_streak(self):
        for i in range(3):
            d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.habit.records[d] = "done"
        self.assertEqual(self.habit.get_current_streak(), 3)

    def test_current_streak_broken(self):
        self.habit.records[date.today().strftime("%Y-%m-%d")] = "done"
        yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.habit.records[yesterday] = "skipped"
        self.assertEqual(self.habit.get_current_streak(), 1)

    def test_best_streak(self):
        for i in range(7):
            d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.habit.records[d] = "done"
        self.habit.records[(date.today() - timedelta(days=7)).strftime("%Y-%m-%d")] = "skipped"
        for i in range(8, 10):
            d = (date.today() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.habit.records[d] = "done"
        self.assertEqual(self.habit.get_best_streak(), 7)

    def test_stats(self):
        self.habit.records["2026-06-01"] = "done"
        self.habit.records["2026-06-02"] = "skipped"
        self.habit.records["2026-06-03"] = "done"
        stats = self.habit.get_stats()
        self.assertEqual(stats['total_days'], 3)
        self.assertEqual(stats['done'], 2)
        self.assertEqual(stats['skipped'], 1)
        self.assertAlmostEqual(stats['completion_rate'], 66.7, places=1)

    def test_to_dict_and_from_dict(self):
        self.habit.records["2026-06-01"] = "done"
        data = self.habit.to_dict()
        restored = Habit.from_dict(data)
        self.assertEqual(restored.name, "Бег")
        self.assertEqual(restored.records["2026-06-01"], "done")


class TestHabitStorage(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_habits.json"
        self.storage = HabitStorage(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load(self):
        habits = [
            Habit(id="1", name="Бег"),
            Habit(id="2", name="Чтение")
        ]
        habits[0].records["2026-06-01"] = "done"

        self.assertTrue(self.storage.save(habits))
        loaded = self.storage.load()

        self.assertEqual(len(loaded), 2)
        self.assertEqual(loaded[0].name, "Бег")
        self.assertEqual(loaded[0].records["2026-06-01"], "done")

    def test_export_import_csv(self):
        habits = [Habit(id="1", name="Тест")]
        habits[0].records["2026-06-01"] = "done"
        habits[0].records["2026-06-02"] = "skipped"

        csv_file = "test_export.csv"
        self.assertTrue(self.storage.export_to_csv(habits, csv_file))
        self.assertTrue(os.path.exists(csv_file))

        imported = self.storage.import_from_csv(csv_file)
        self.assertEqual(len(imported), 1)
        self.assertEqual(imported[0].name, "Тест")
        self.assertEqual(imported[0].records["2026-06-01"], "done")

        os.remove(csv_file)


if __name__ == "__main__":
    unittest.main()