# modules/habit_tracker/models.py
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional


@dataclass
class Habit:
    """Модель привычки"""
    id: str
    name: str
    color: str = "#4a9eff"
    created_at: str = ""
    records: dict = field(default_factory=dict)  # date (YYYY-MM-DD) -> status

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().strftime("%Y-%m-%d")

    def get_status_for_date(self, date_str: str) -> Optional[str]:
        """Получить статус за дату"""
        return self.records.get(date_str)

    def mark_date(self, date_str: str, status: str) -> bool:
        """Отметить день. Возвращает False, если уже отмечен."""
        if date_str in self.records:
            return False
        self.records[date_str] = status
        return True

    def update_status(self, date_str: str, status: str):
        """Принудительно обновить статус."""
        self.records[date_str] = status

    def get_current_streak(self) -> int:
        """Текущая серия дней подряд (до сегодня включительно)."""
        today = date.today()
        streak = 0
        check_date = today

        while True:
            date_str = check_date.strftime("%Y-%m-%d")
            if date_str < self.created_at:
                break
            status = self.records.get(date_str)
            if status == "done":
                streak += 1
                check_date = check_date - timedelta(days=1)
            else:
                break

        return streak

    def get_best_streak(self) -> int:
        """Лучшая серия за все время."""
        if not self.records:
            return 0

        sorted_dates = sorted(self.records.keys())
        best = 0
        current = 0

        for i, date_str in enumerate(sorted_dates):
            if self.records[date_str] == "done":
                if i > 0:
                    prev_date = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d").date()
                    curr_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if (curr_date - prev_date).days != 1:
                        current = 0
                current += 1
                best = max(best, current)
            else:
                current = 0

        return best

    def get_stats(self) -> dict:
        """Полная статистика по привычке."""
        total = len(self.records)
        done = sum(1 for s in self.records.values() if s == "done")
        skipped = sum(1 for s in self.records.values() if s == "skipped")
        missed = sum(1 for s in self.records.values() if s == "missed")

        return {
            "total_days": total,
            "done": done,
            "skipped": skipped,
            "missed": missed,
            "completion_rate": round(done / total * 100, 1) if total > 0 else 0,
            "current_streak": self.get_current_streak(),
            "best_streak": self.get_best_streak()
        }

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color,
            "created_at": self.created_at,
            "records": self.records
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        """Десериализация из словаря."""
        return cls(**data)