# modules/notes_app/widget.py
import uuid

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QLineEdit, QTextEdit, QComboBox, QFrame, QFileDialog, QMessageBox, QListWidget,
                             QListWidgetItem, QSplitter)

from .models import Note, NotesEngine
from .storage import NotesStorage


class NoteCard(QFrame):
    """Карточка заметки в списке"""

    def __init__(self, note: Note, parent=None):
        super().__init__(parent)
        self.note = note
        self.setStyleSheet("""
            QFrame {
                background-color: #2d2d44;
                border-radius: 8px;
                padding: 10px;
                border-left: 4px solid #4a9eff;
            }
        """)
        self._create_ui()

    def _create_ui(self):
        layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel(self.note.title)
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Категория и дата
        meta = QLabel(f"📁 {self.note.category} • 🕐 {self.note.updated_at}")
        meta.setStyleSheet("color: #a0a0b0; font-size: 10px;")
        layout.addWidget(meta)

        # Превью контента
        preview = self.note.content[:100] + "..." if len(self.note.content) > 100 else self.note.content
        content_label = QLabel(preview)
        content_label.setStyleSheet("color: #d0d0d0; font-size: 11px;")
        content_label.setWordWrap(True)
        layout.addWidget(content_label)

        # Теги
        if self.note.tags:
            tags_label = QLabel("🏷️ " + ", ".join(self.note.tags))
            tags_label.setStyleSheet("color: #fbbf24; font-size: 10px;")
            layout.addWidget(tags_label)


class NotesWidget(QWidget):
    """Главный виджет приложения заметок"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.storage = NotesStorage()
        self.notes, self.categories = self.storage.load()
        self.engine = NotesEngine(self.notes, self.categories)
        self.current_note = None
        self._create_ui()
        self._refresh_list()

    def _create_ui(self):
        main_layout = QVBoxLayout(self)

        # Заголовок
        title = QLabel("📓 Заметки")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #4a9eff;")
        main_layout.addWidget(title)

        # Разделитель с списком и редактором
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Левая панель - список заметок
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        # Поиск
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск заметок...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_input)
        left_layout.addLayout(search_layout)

        # Фильтр по категории
        self.category_filter = QComboBox()
        self.category_filter.addItem("Все категории")
        self.category_filter.addItems(self.engine.get_all_categories())
        self.category_filter.currentTextChanged.connect(self._on_category_filter)
        self.category_filter.setStyleSheet("""
            QComboBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        left_layout.addWidget(self.category_filter)

        # Список заметок
        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet("""
            QListWidget {
                background-color: #1e1e2e;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #383854;
            }
            QListWidget::item:selected {
                background-color: #4a9eff;
            }
        """)
        self.notes_list.itemClicked.connect(self._on_note_selected)
        left_layout.addWidget(self.notes_list)

        # Кнопки управления
        btn_layout = QHBoxLayout()

        btn_new = QPushButton("➕ Новая")
        btn_new.clicked.connect(self._new_note)
        btn_layout.addWidget(btn_new)

        btn_delete = QPushButton("🗑️ Удалить")
        btn_delete.clicked.connect(self._delete_note)
        btn_layout.addWidget(btn_delete)

        left_layout.addLayout(btn_layout)

        splitter.addWidget(left_panel)

        # Правая панель - редактор
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # Заголовок заметки
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Заголовок заметки...")
        self.title_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        right_layout.addWidget(self.title_input)

        # Категория и теги
        meta_layout = QHBoxLayout()

        self.category_combo = QComboBox()
        self.category_combo.addItems(self.engine.get_all_categories())
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        meta_layout.addWidget(QLabel("Категория:"))
        meta_layout.addWidget(self.category_combo)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Теги через запятую...")
        self.tags_input.setStyleSheet("""
            QLineEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 5px;
            }
        """)
        meta_layout.addWidget(QLabel("🏷️ Теги:"))
        meta_layout.addWidget(self.tags_input)

        right_layout.addLayout(meta_layout)

        # Редактор контента
        self.content_editor = QTextEdit()
        self.content_editor.setPlaceholderText("Начните писать заметку...")
        self.content_editor.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d44;
                color: white;
                border: 1px solid #383854;
                border-radius: 4px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        right_layout.addWidget(self.content_editor)

        # Кнопки сохранения и экспорта
        save_layout = QHBoxLayout()

        btn_save = QPushButton("💾 Сохранить")
        btn_save.clicked.connect(self._save_note)
        save_layout.addWidget(btn_save)

        btn_export_all = QPushButton("📦 Экспорт всех (TXT)")
        btn_export_all.clicked.connect(self._export_all_txt)
        save_layout.addWidget(btn_export_all)

        save_layout.addStretch()
        right_layout.addLayout(save_layout)

        # Статистика
        self.stats_label = QLabel("📊 Статистика: 0 заметок")
        self.stats_label.setStyleSheet("color: #a0a0b0; padding: 5px;")
        right_layout.addWidget(self.stats_label)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 700])

        main_layout.addWidget(splitter)

        # Обновить статистику
        self._update_stats()

    def _refresh_list(self, notes: list = None):
        """Обновить список заметок"""
        self.notes_list.clear()

        display_notes = notes if notes is not None else self.notes

        if not display_notes:
            item = QListWidgetItem("Нет заметок. Создайте первую!")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            self.notes_list.addItem(item)
        else:
            for note in sorted(display_notes, key=lambda n: n.updated_at, reverse=True):
                item = QListWidgetItem()
                card = NoteCard(note)
                item.setSizeHint(card.sizeHint())
                self.notes_list.addItem(item)
                self.notes_list.setItemWidget(item, card)

        self._update_stats()

    def _on_note_selected(self, item):
        """Выбор заметки из списка"""
        if item is None:
            return

        # Найти заметку по индексу
        index = self.notes_list.row(item)
        if index < 0 or index >= len(self.notes):
            return

        note = self.notes[index]
        self.current_note = note

        # Заполнить поля
        self.title_input.setText(note.title)
        self.content_editor.setText(note.content)

        # Установить категорию
        cat_index = self.category_combo.findText(note.category)
        if cat_index >= 0:
            self.category_combo.setCurrentIndex(cat_index)

        # Установить теги
        self.tags_input.setText(", ".join(note.tags))

    def _on_search(self, text: str):
        """Поиск заметок"""
        if not text:
            self._refresh_list()
            return

        results = self.engine.search_notes(text)
        self._refresh_list(results)

    def _on_category_filter(self, category: str):
        """Фильтр по категории"""
        if category == "Все категории":
            self._refresh_list()
            return

        results = self.engine.get_notes_by_category(category)
        self._refresh_list(results)

    def _new_note(self):
        """Создать новую заметку"""
        self.current_note = None
        self.title_input.clear()
        self.content_editor.clear()
        self.tags_input.clear()
        self.category_combo.setCurrentIndex(0)
        self.title_input.setFocus()

    def _save_note(self):
        """Сохранить заметку"""
        title = self.title_input.text().strip()
        content = self.content_editor.toPlainText()
        category = self.category_combo.currentText()
        tags = [t.strip() for t in self.tags_input.text().split(",") if t.strip()]

        if not title:
            QMessageBox.warning(self, "Ошибка", "Введите заголовок заметки")
            return

        if not content:
            QMessageBox.warning(self, "Ошибка", "Введите содержимое заметки")
            return

        if self.current_note:
            # Обновить существующую
            self.engine.update_note(self.current_note.id, title, content, category)
            self.current_note.tags = tags
            QMessageBox.information(self, "Успех", "Заметка обновлена!")
        else:
            # Создать новую
            note = Note(
                id=str(uuid.uuid4()),
                title=title,
                content=content,
                category=category,
                tags=tags
            )
            self.engine.add_note(note)
            self.current_note = note
            QMessageBox.information(self, "Успех", "Заметка создана!")

        # Сохранить и обновить список
        self.storage.save(self.notes, self.categories)
        self._refresh_list()

    def _delete_note(self):
        """Удалить заметку"""
        if not self.current_note:
            QMessageBox.warning(self, "Внимание", "Выберите заметку для удаления")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить заметку '{self.current_note.title}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.engine.delete_note(self.current_note.id)
            self.storage.save(self.notes, self.categories)
            self._new_note()
            self._refresh_list()
            QMessageBox.information(self, "Успех", "Заметка удалена!")

    def _export_all_txt(self):
        """Экспорт всех заметок в TXT"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Экспорт всех заметок", "all_notes.txt", "Text Files (*.txt)"
        )

        if filepath:
            if self.engine.export_all_to_txt(filepath):
                QMessageBox.information(self, "Успех", f"Экспортировано {len(self.notes)} заметок в {filepath}")

    def _update_stats(self):
        """Обновить статистику"""
        stats = self.engine.get_stats()
        self.stats_label.setText(
            f"📊 Всего заметок: {stats['total_notes']} | "
            f"Слов: {stats['total_words']} | "
            f"Символов: {stats['total_chars']}"
        )