# modules/schedule/tests/test_schedule.py
import unittest

from modules.schedule.models import Lesson, ScheduleEngine, DayOfWeek
from modules.schedule.storage import ScheduleStorage


class TestLesson(unittest.TestCase):
    def test_create_lesson(self):
        lesson = Lesson(
            id="1",
            name="Математика",
            day_of_week=0,
            start_time="09:00",
            end_time="10:30"
        )
        self.assertEqual(lesson.name, "Математика")
        self.assertEqual(lesson.get_duration_minutes(), 90)

    def test_invalid_time(self):
        with self.assertRaises(ValueError):
            Lesson(
                id="2",
                name="Invalid",
                day_of_week=0,
                start_time="10:00",
                end_time="09:00"
            )

    def test_get_type_name(self):
        lesson = Lesson(
            id="3",
            name="Test",
            day_of_week=1,
            start_time="10:00",
            end_time="11:00",
            lesson_type="PRACTICE"
        )
        self.assertEqual(lesson.get_type_name(), "Практика")


class TestScheduleEngine(unittest.TestCase):
    def setUp(self):
        self.lessons = [
            Lesson(id="1", name="Math", day_of_week=0, start_time="09:00", end_time="10:30"),
            Lesson(id="2", name="Physics", day_of_week=0, start_time="11:00", end_time="12:30"),
            Lesson(id="3", name="History", day_of_week=1, start_time="10:00", end_time="11:30"),
        ]
        self.engine = ScheduleEngine(self.lessons)

    def test_get_lessons_for_day(self):
        monday_lessons = self.engine.get_lessons_for_day(DayOfWeek.MONDAY)
        self.assertEqual(len(monday_lessons), 2)

        tuesday_lessons = self.engine.get_lessons_for_day(DayOfWeek.TUESDAY)
        self.assertEqual(len(tuesday_lessons), 1)

    def test_get_weekly_load(self):
        load = self.engine.get_weekly_load()
        self.assertIn("Понедельник", load)
        self.assertEqual(load["Понедельник"]["lessons_count"], 2)

    def test_total_weekly_hours(self):
        total = self.engine.get_total_weekly_hours()
        self.assertGreater(total, 0)


class TestScheduleStorage(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_schedule.json"
        self.storage = ScheduleStorage(self.test_file)
        self.lessons = [
            Lesson(id="1", name="Test", day_of_week=0, start_time="09:00", end_time="10:00")
        ]

    def tearDown(self):
        import os
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load(self):
        self.storage.save(self.lessons)
        loaded = self.storage.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, "Test")

    def test_has_conflict(self):
        lesson1 = Lesson(id="1", name="L1", day_of_week=0, start_time="09:00", end_time="10:00")
        lesson2 = Lesson(id="2", name="L2", day_of_week=0, start_time="09:30", end_time="10:30")

        self.assertTrue(self.storage._has_conflict([lesson1], lesson2))

        lesson3 = Lesson(id="3", name="L3", day_of_week=0, start_time="10:00", end_time="11:00")
        self.assertFalse(self.storage._has_conflict([lesson1], lesson3))


if __name__ == "__main__":
    unittest.main()