# modules/notes_app/tests/test_notes.py
import os
import unittest

from modules.notes_app.models import Note, Category, NotesEngine
from modules.notes_app.storage import NotesStorage


class TestNote(unittest.TestCase):
    def test_create_note(self):
        note = Note(
            id="1",
            title="Тестовая заметка",
            content="Это тестовый контент"
        )
        self.assertEqual(note.title, "Тестовая заметка")
        self.assertEqual(note.get_word_count(), 3)
        self.assertEqual(note.get_char_count(), 20)

    def test_update_content(self):
        note = Note(id="2", title="Test", content="Old content")
        note.update_content("New content")
        self.assertEqual(note.content, "New content")

    def test_tags(self):
        note = Note(id="3", title="Test", content="Content")
        note.add_tag("python")
        note.add_tag("code")
        self.assertIn("python", note.tags)
        self.assertIn("code", note.tags)

        note.remove_tag("python")
        self.assertNotIn("python", note.tags)

    def test_to_dict_and_from_dict(self):
        note = Note(
            id="4",
            title="Test",
            content="Content",
            category="Work",
            tags=["tag1", "tag2"]
        )
        data = note.to_dict()
        restored = Note.from_dict(data)
        self.assertEqual(restored.title, "Test")
        self.assertEqual(restored.tags, ["tag1", "tag2"])


class TestNotesEngine(unittest.TestCase):
    def setUp(self):
        self.notes = [
            Note(id="1", title="Note 1", content="Content 1", category="Work"),
            Note(id="2", title="Note 2", content="Content 2", category="Personal"),
            Note(id="3", title="Python Guide", content="Learn Python programming", category="Study", tags=["python"]),
        ]
        self.categories = [
            Category(id="c1", name="Work", color="#4a9eff"),
            Category(id="c2", name="Personal", color="#4ade80"),
            Category(id="c3", name="Study", color="#fbbf24"),
        ]
        self.engine = NotesEngine(self.notes, self.categories)

    def test_add_note(self):
        new_note = Note(id="4", title="New", content="New content")
        self.assertTrue(self.engine.add_note(new_note))
        self.assertEqual(len(self.notes), 4)

    def test_update_note(self):
        self.assertTrue(self.engine.update_note("1", "Updated", "New content", "Work"))
        note = self.engine.get_note("1")
        self.assertEqual(note.title, "Updated")

    def test_delete_note(self):
        self.assertTrue(self.engine.delete_note("1"))
        self.assertEqual(len(self.notes), 2)

    def test_get_notes_by_category(self):
        work_notes = self.engine.get_notes_by_category("Work")
        self.assertEqual(len(work_notes), 1)
        self.assertEqual(work_notes[0].title, "Note 1")

    def test_search_notes(self):
        results = self.engine.search_notes("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python Guide")

    def test_get_notes_by_tag(self):
        results = self.engine.get_notes_by_tag("python")
        self.assertEqual(len(results), 1)

    def test_get_stats(self):
        stats = self.engine.get_stats()
        self.assertEqual(stats["total_notes"], 3)
        self.assertGreater(stats["total_words"], 0)

    def test_export_all_to_txt(self):
        filepath = "test_all_notes.txt"
        self.assertTrue(self.engine.export_all_to_txt(filepath))
        self.assertTrue(os.path.exists(filepath))
        os.remove(filepath)


class TestNotesStorage(unittest.TestCase):
    def setUp(self):
        self.test_file = "test_notes.json"
        self.storage = NotesStorage(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_load(self):
        notes = [Note(id="1", title="Test", content="Content")]
        categories = [Category(id="c1", name="Test", color="#fff")]

        self.assertTrue(self.storage.save(notes, categories))

        loaded_notes, loaded_cats = self.storage.load()
        self.assertEqual(len(loaded_notes), 1)
        self.assertEqual(len(loaded_cats), 1)

    def test_default_categories(self):
        notes, categories = self.storage.load()
        self.assertGreater(len(categories), 0)


if __name__ == "__main__":
    unittest.main()