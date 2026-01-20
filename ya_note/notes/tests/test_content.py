"""Тесты контента, списки заметок и формы на страницах."""

from notes.forms import NoteForm
from notes.tests.common import (
    BaseNoteTestCase,
    NOTE_SLUG,
    NOTE_TEXT,
    NOTE_TITLE,
    NOTES_ADD_URL,
    NOTES_EDIT_URL,
    NOTES_LIST_URL,
)


class TestContent(BaseNoteTestCase):
    """Проверяет, что страницы отдают ожидаемые данные в контексте."""

    def test_note_visible_in_list_for_author(self):
        """Автор видит свою заметку в списке."""
        response = self.author_client.get(NOTES_LIST_URL)
        notes = response.context["object_list"]

        note = notes.get(slug=NOTE_SLUG)
        assert note.title == NOTE_TITLE
        assert note.text == NOTE_TEXT
        assert note.slug == NOTE_SLUG
        assert note.author_id == self.author.id

    def test_note_hidden_in_list_for_other_user(self):
        """Чужие заметки не попадают в список другого пользователя."""
        response = self.reader_client.get(NOTES_LIST_URL)
        notes = response.context["object_list"]

        assert not notes.filter(slug=NOTE_SLUG).exists()

    def test_pages_have_form(self):
        """На страницах создания и редактирования заметки есть форма."""
        for url in (NOTES_ADD_URL, NOTES_EDIT_URL):
            with self.subTest(url=url):
                form = self.author_client.get(url).context.get("form")
                assert isinstance(form, NoteForm)
