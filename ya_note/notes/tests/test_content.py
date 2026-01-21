"""Тесты контента, списки заметок и формы на страницах."""

from notes.forms import NoteForm
from notes.tests.common import (
    BaseNoteTestCase,
    NOTES_ADD_URL,
    NOTES_EDIT_URL,
    NOTES_LIST_URL,
)


class TestContent(BaseNoteTestCase):
    """Проверяет, что страницы отдают ожидаемые данные в контексте."""

    def test_note_visible_in_list_for_author(self):
        """Автор видит свою заметку в списке."""
        notes = self.author_client.get(NOTES_LIST_URL).context["object_list"]
        self.assertIn(self.note, notes)

        note = notes.get(pk=self.note.pk)
        self.assertEqual(note.title, self.note.title)
        self.assertEqual(note.text, self.note.text)
        self.assertEqual(note.slug, self.note.slug)
        self.assertEqual(note.author, self.note.author)

    def test_note_hidden_in_list_for_other_user(self):
        """Чужие заметки не попадают в список другого пользователя."""
        self.assertNotIn(
            self.note,
            self.reader_client.get(NOTES_LIST_URL).context["object_list"],
        )

    def test_pages_have_form(self):
        """На страницах создания и редактирования заметки есть форма."""
        for url in (NOTES_ADD_URL, NOTES_EDIT_URL):
            with self.subTest(url=url):
                self.assertIsInstance(
                    self.author_client.get(url).context.get("form"),
                    NoteForm,
                )
