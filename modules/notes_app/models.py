# modules/notes_app/models.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List


@dataclass
class Note:
    """Модель заметки"""
    id: str
    title: str
    content: str
    category: str = "Общее"
    created_at: str = ""
    updated_at: str = ""
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def update_content(self, content: str):
        """Обновить содержимое заметки"""
        self.content = content
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def update_title(self, title: str):
        """Обновить заголовок"""
        self.title = title
        self.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def add_tag(self, tag: str):
        """Добавить тег"""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Удалить тег"""
        if tag in self.tags:
            self.tags.remove(tag)

    def get_word_count(self) -> int:
        """Количество слов в заметке"""
        return len(self.content.split())

    def get_char_count(self) -> int:
        """Количество символов"""
        return len(self.content)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "category": self.category,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Note":
        return cls(**data)


@dataclass
class Category:
    """Модель категории"""
    id: str
    name: str
    color: str = "#4a9eff"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "color": self.color
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(**data)


class NotesEngine:
    """Движок управления заметками"""

    def __init__(self, notes: List[Note], categories: List[Category]):
        self.notes = notes
        self.categories = categories

    def add_note(self, note: Note) -> bool:
        """Добавить заметку"""
        self.notes.append(note)
        return True

    def update_note(self, note_id: str, title: str, content: str, category: str) -> bool:
        """Обновить заметку"""
        for note in self.notes:
            if note.id == note_id:
                note.update_title(title)
                note.update_content(content)
                note.category = category
                return True
        return False

    def delete_note(self, note_id: str) -> bool:
        """Удалить заметку"""
        for i, note in enumerate(self.notes):
            if note.id == note_id:
                self.notes.pop(i)
                return True
        return False

    def get_note(self, note_id: str) -> Optional[Note]:
        """Получить заметку по ID"""
        for note in self.notes:
            if note.id == note_id:
                return note
        return None

    def get_notes_by_category(self, category: str) -> List[Note]:
        """Получить заметки по категории"""
        return [n for n in self.notes if n.category == category]

    def search_notes(self, query: str) -> List[Note]:
        """Поиск заметок по тексту"""
        query_lower = query.lower()
        return [
            n for n in self.notes
            if query_lower in n.title.lower() or query_lower in n.content.lower()
        ]

    def get_notes_by_tag(self, tag: str) -> List[Note]:
        """Получить заметки по тегу"""
        return [n for n in self.notes if tag in n.tags]

    def get_all_categories(self) -> List[str]:
        """Получить список всех категорий"""
        return [c.name for c in self.categories]

    def add_category(self, category: Category) -> bool:
        """Добавить категорию"""
        self.categories.append(category)
        return True

    def get_stats(self) -> dict:
        """Статистика по заметкам"""
        total_notes = len(self.notes)
        total_words = sum(n.get_word_count() for n in self.notes)
        total_chars = sum(n.get_char_count() for n in self.notes)

        categories_count = {}
        for note in self.notes:
            cat = note.category
            categories_count[cat] = categories_count.get(cat, 0) + 1

        return {
            "total_notes": total_notes,
            "total_words": total_words,
            "total_chars": total_chars,
            "categories_count": categories_count
        }

    def export_all_to_txt(self, filepath: str) -> bool:
        """Экспорт всех заметок в TXT"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                for note in self.notes:
                    f.write(f"{'=' * 50}\n")
                    f.write(f"ЗАМЕТКА: {note.title}\n")
                    f.write(f"Категория: {note.category}\n")
                    f.write(f"Создано: {note.created_at}\n")
                    f.write(f"{'=' * 50}\n\n")
                    f.write(note.content)
                    f.write("\n\n")
            return True
        except (IOError, OSError) as e:
            print(f"Ошибка экспорта: {e}")
            return False