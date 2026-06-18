# modules/schedule/storage.py
import json
from pathlib import Path
from typing import List

from .models import Lesson


def _serialize_lesson(lesson: Lesson) -> dict:
    """Сериализация занятия в словарь (общая функция)."""
    return lesson.to_dict()


def _deserialize_lesson(data: dict) -> Lesson:
    """Десериализация занятия из словаря (общая функция)."""
    return Lesson.from_dict(data)


class ScheduleStorage:
    """Хранение расписания в JSON"""

    def __init__(self, filepath: str = "schedule_data.json"):
        self.filepath = Path(filepath)

    def save(self, lessons: List[Lesson]) -> bool:
        """Сохранить расписание"""
        try:
            data = [_serialize_lesson(l) for l in lessons]
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError, json.JSONEncodeError) as e:  # ← Конкретные исключения
            print(f"Ошибка сохранения расписания: {e}")
            return False

    def load(self) -> List[Lesson]:
        """Загрузить расписание"""
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [_deserialize_lesson(item) for item in data]
        except (IOError, OSError, json.JSONDecodeError, KeyError) as e:  # ← Конкретные исключения
            print(f"Ошибка загрузки расписания: {e}")
            return []

    def add_lesson(self, lessons: List[Lesson], lesson: Lesson) -> bool:
        """Добавить занятие с проверкой на пересечения"""
        if self._has_conflict(lessons, lesson):
            return False
        lessons.append(lesson)
        return self.save(lessons)

    def update_lesson(self, lessons: List[Lesson], lesson_id: str, updated_lesson: Lesson) -> bool:
        """Обновить занятие"""
        for i, l in enumerate(lessons):
            if l.id == lesson_id:
                lessons[i] = updated_lesson
                return self.save(lessons)
        return False

    def delete_lesson(self, lessons: List[Lesson], lesson_id: str) -> bool:
        """Удалить занятие"""
        for i, l in enumerate(lessons):
            if l.id == lesson_id:
                lessons.pop(i)
                return self.save(lessons)
        return False

    @staticmethod  # ← Добавлено: метод не использует self
    def _has_conflict(lessons: List[Lesson], new_lesson: Lesson) -> bool:
        """Проверить на пересечение по времени"""
        day_lessons = [l for l in lessons if l.day_of_week == new_lesson.day_of_week]

        new_start = new_lesson.get_start_time_obj()
        new_end = new_lesson.get_end_time_obj()

        for lesson in day_lessons:
            lesson_start = lesson.get_start_time_obj()
            lesson_end = lesson.get_end_time_obj()

            # Проверяем пересечение
            if new_start < lesson_end and new_end > lesson_start:
                return True

        return False

    @staticmethod  # ← Добавлено: метод не использует self
    def export_to_ics(lessons: List[Lesson], filepath: str) -> bool:
        """Экспорт в формат iCalendar"""
        try:
            from datetime import datetime
            import uuid

            ics_content = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//SuperApp//Schedule//RU",
            ]

            for lesson in lessons:
                day_offset = lesson.day_of_week - datetime.now().weekday()
                if day_offset < 0:
                    day_offset += 7

                start_date = datetime.now().date() + __import__('datetime').timedelta(days=day_offset)
                end_date = start_date

                start_time = lesson.get_start_time_obj()
                end_time = lesson.get_end_time_obj()

                start_dt = datetime.combine(start_date, start_time)
                end_dt = datetime.combine(end_date, end_time)

                ics_content.extend([
                    "BEGIN:VEVENT",
                    f"UID:{uuid.uuid4()}@superapp",
                    f"DTSTART:{start_dt.strftime('%Y%m%dT%H%M%S')}",
                    f"DTEND:{end_dt.strftime('%Y%m%dT%H%M%S')}",
                    f"SUMMARY:{lesson.name}",
                    f"DESCRIPTION:{lesson.description}",
                    f"LOCATION:{lesson.classroom}",
                    "END:VEVENT",
                ])

            ics_content.append("END:VCALENDAR")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\r\n'.join(ics_content))

            return True
        except (IOError, OSError, json.JSONDecodeError) as e:  # ← Конкретные исключения
            print(f"Ошибка экспорта в ICS: {e}")
            return False