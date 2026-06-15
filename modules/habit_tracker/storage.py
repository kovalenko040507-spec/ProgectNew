# modules/habit_tracker/storage.py
import json
import uuid
from pathlib import Path
from typing import List

from .models import Habit


def export_to_csv(habits: List[Habit], filepath: str) -> bool:
    """Экспорт привычек в CSV."""
    try:
        import csv
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Привычка", "Дата", "Статус"])
            for habit in habits:
                for date_str, status in sorted(habit.records.items()):
                    writer.writerow([habit.name, date_str, status])
        return True
    except Exception as e:
        print(f"Ошибка экспорта: {e}")
        return False


def import_from_csv(filepath: str) -> List[Habit]:
    """Импорт привычек из CSV."""
    try:
        import csv
        habits_dict = {}
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row["Привычка"]
                if name not in habits_dict:
                    habits_dict[name] = Habit(
                        id=str(uuid.uuid4()),
                        name=name
                    )
                habits_dict[name].records[row["Дата"]] = row["Статус"]
        return list(habits_dict.values())
    except Exception as e:
        print(f"Ошибка импорта: {e}")
        return []


class HabitStorage:
    """Хранение привычек в JSON"""

    def __init__(self, filepath: str = "habits_data.json"):
        self.filepath = Path(filepath)

    def save(self, habits: List[Habit]) -> bool:
        """Сохранить список привычек."""
        try:
            data = [h.to_dict() for h in habits]
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            return False

    def load(self) -> List[Habit]:
        """Загрузить список привычек."""
        if not self.filepath.exists():
            return []
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [Habit.from_dict(item) for item in data]
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return []

    def export_to_csv(self, habits, filepath):
        pass

    def import_from_csv(self, csv_file):
        pass

    