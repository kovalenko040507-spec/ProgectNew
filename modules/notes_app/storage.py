# modules/notes_app/storage.py
import json
from pathlib import Path
from typing import List

from .models import Note, Category


def _get_default_categories() -> List[Category]:
    """Получить категории по умолчанию"""
    colors = ["#4a9eff", "#4ade80", "#fbbf24", "#f87171", "#a78bfa", "#fb923c"]
    default_cats = ["Общее", "Работа", "Учёба", "Идеи", "Важное", "Личное"]

    return [
        Category(id=str(__import__('uuid').uuid4()), name=name, color=colors[i])
        for i, name in enumerate(default_cats)
    ]


class NotesStorage:
    """Хранение заметок в JSON"""

    def __init__(self, filepath: str = "notes_data.json"):
        self.filepath = Path(filepath)

    def save(self, notes: List[Note], categories: List[Category]) -> bool:
        """Сохранить все данные"""
        try:
            data = {
                "notes": [n.to_dict() for n in notes],
                "categories": [c.to_dict() for c in categories]
            }
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except (IOError, OSError, json.JSONEncodeError) as e:
            print(f"Ошибка сохранения заметок: {e}")
            return False

    def load(self) -> tuple:
        """Загрузить все данные"""
        if not self.filepath.exists():
            return [], _get_default_categories()
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            notes = [Note.from_dict(n) for n in data.get("notes", [])]
            categories = [Category.from_dict(c) for c in data.get("categories", [])]

            return notes, categories
        except (IOError, OSError, json.JSONDecodeError, KeyError) as e:
            print(f"Ошибка загрузки заметок: {e}")
            return [], _get_default_categories()


