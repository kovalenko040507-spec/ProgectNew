# modules/schedule/models.py
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import List


class DayOfWeek(Enum):
    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @classmethod
    def from_int(cls, day: int) -> "DayOfWeek":
        return cls(day % 7)

    @classmethod
    def from_datetime(cls, dt: datetime) -> "DayOfWeek":
        return cls(dt.weekday())

    def get_name_ru(self) -> str:
        names = {
            DayOfWeek.MONDAY: "Понедельник",
            DayOfWeek.TUESDAY: "Вторник",
            DayOfWeek.WEDNESDAY: "Среда",
            DayOfWeek.THURSDAY: "Четверг",
            DayOfWeek.FRIDAY: "Пятница",
            DayOfWeek.SATURDAY: "Суббота",
            DayOfWeek.SUNDAY: "Воскресенье"
        }
        return names.get(self, "Неизвестно")


class LessonType(Enum):
    LECTURE = "Лекция"
    PRACTICE = "Практика"
    LAB = "Лабораторная"
    SEMINAR = "Семинар"
    EXAM = "Экзамен"
    CONSULTATION = "Консультация"


class LessonStatus(Enum):
    SCHEDULED = "Запланировано"
    IN_PROGRESS = "Идёт"
    COMPLETED = "Завершено"
    CANCELLED = "Отменено"


@dataclass
class Lesson:
    """Модель занятия"""
    id: str
    name: str
    day_of_week: int  # 0-6 (понедельник-воскресенье)
    start_time: str  # формат "HH:MM"
    end_time: str  # формат "HH:MM"
    lesson_type: str = "LECTURE"
    classroom: str = ""
    description: str = ""
    status: str = "SCHEDULED"

    def __post_init__(self):
        # Валидация времени
        if not self._validate_time():
            raise ValueError("Время окончания должно быть позже времени начала")

    def _validate_time(self) -> bool:
        try:
            start = datetime.strptime(self.start_time, "%H:%M").time()
            end = datetime.strptime(self.end_time, "%H:%M").time()
            return end > start
        except:
            return False

    def get_start_time_obj(self) -> time:
        return datetime.strptime(self.start_time, "%H:%M").time()

    def get_end_time_obj(self) -> time:
        return datetime.strptime(self.end_time, "%H:%M").time()

    def get_duration_minutes(self) -> int:
        start = self.get_start_time_obj()
        end = self.get_end_time_obj()
        return (end.hour * 60 + end.minute) - (start.hour * 60 + start.minute)

    def get_type_name(self) -> str:
        try:
            return LessonType[self.lesson_type].value
        except KeyError:
            return self.lesson_type

    def get_status_name(self) -> str:
        try:
            return LessonStatus[self.status].value
        except KeyError:
            return self.status

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "lesson_type": self.lesson_type,
            "classroom": self.classroom,
            "description": self.description,
            "status": self.status
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Lesson":
        return cls(**data)


class ScheduleEngine:
    """Движок расписания"""

    def __init__(self, lessons: list):  # ← Исправление: убрать типизацию или добавить импорт
        self.lessons = lessons

    def get_lessons_for_day(self, day: DayOfWeek) -> list:  # ← Вернуть list вместо List
        """Получить занятия для конкретного дня недели"""
        return sorted(
            [l for l in self.lessons if l.day_of_week == day.value and l.status != "CANCELLED"],
            key=lambda x: x.start_time
        )

    def get_next_lesson(self, from_time=None) -> object:  # ← Убрать Optional[Lesson] или добавить импорт
        """Получить следующее занятие от текущего времени"""
        if from_time is None:
            from_time = datetime.now()

        current_day = DayOfWeek.from_datetime(from_time)
        current_time = from_time.time()

        # Ищем занятия сегодня
        today_lessons = self.get_lessons_for_day(current_day)
        for lesson in today_lessons:
            lesson_start = lesson.get_start_time_obj()
            if lesson_start > current_time:
                return lesson

        # Ищем занятия в ближайшие дни
        for i in range(1, 8):
            next_day = DayOfWeek.from_int((current_day.value + i) % 7)
            next_day_lessons = self.get_lessons_for_day(next_day)
            if next_day_lessons:
                return next_day_lessons[0]

        return None

    @staticmethod  # ← Добавлено: метод не использует self
    def get_time_until_next_lesson(lesson: Lesson, from_time=None) -> timedelta:
        """Получить время до следующего занятия"""
        if from_time is None:
            from_time = datetime.now()

        lesson_day = DayOfWeek(lesson.day_of_week)
        lesson_time = lesson.get_start_time_obj()

        # Вычисляем дату следующего занятия
        days_ahead = lesson_day.value - from_time.weekday()
        if days_ahead < 0:
            days_ahead += 7

        # Если сегодня, проверяем время
        if days_ahead == 0 and lesson_time <= from_time.time():
            days_ahead = 7

        next_lesson_datetime = datetime.combine(
            from_time.date() + timedelta(days=days_ahead),
            lesson_time
        )

        return next_lesson_datetime - from_time

    def get_weekly_load(self) -> dict:
        """Получить учебную нагрузку по дням"""
        load = {}
        for day in DayOfWeek:
            lessons = self.get_lessons_for_day(day)
            total_minutes = sum(l.get_duration_minutes() for l in lessons)
            load[day.get_name_ru()] = {
                "lessons_count": len(lessons),
                "total_minutes": total_minutes,
                "total_hours": round(total_minutes / 60, 1)
            }
        return load

    def get_total_weekly_hours(self) -> float:
        """Общее количество часов в неделю"""
        return sum(day_data["total_hours"] for day_data in self.get_weekly_load().values())


@dataclass
class ScheduleDay:
    """Расписание на один день"""
    day: DayOfWeek
    lessons: List[Lesson] = field(default_factory=list)

    def get_total_duration(self) -> int:
        """Общая продолжительность в минутах"""
        return sum(lesson.get_duration_minutes() for lesson in self.lessons)