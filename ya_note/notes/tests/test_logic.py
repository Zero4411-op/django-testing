"""Тесты логики."""

from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.common import (
    BaseNoteTestCase,
    LOGIN_URL,
    NOTE_SLUG,
    NOTES_ADD_URL,
    NOTES_DELETE_URL,
    NOTES_EDIT_URL,
    NOTES_SUCCESS_URL,
)


NEW_NOTE_TITLE = "New title"
NEW_NOTE_TEXT = "New text"
NEW_NOTE_SLUG = "new-slug"

CREATE_FORM_DATA = {
    "title": NEW_NOTE_TITLE,
    "text": NEW_NOTE_TEXT,
    "slug": NEW_NOTE_SLUG,
}

EDIT_FORM_DATA = {
    "title": "Updated title",
    "text": "Updated text",
    "slug": "updated-slug",
}


def notes_state():
    """Cодержимое таблицы заметок для сравнения до и после."""
    return list(
        Note.objects.values("title", "text", "slug", "author_id")
        .order_by("slug")
    )


class TestNoteLogic(BaseNoteTestCase):
    """Проверки создания, slug-правил, редактирования и удаления заметок."""

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        before = notes_state()

        response = self.author_client.post(
            NOTES_ADD_URL, data=CREATE_FORM_DATA
        )
        self.assertRedirects(
            response, NOTES_SUCCESS_URL, fetch_redirect_response=False
        )

        created = Note.objects.get(slug=NEW_NOTE_SLUG)
        assert created.title == NEW_NOTE_TITLE
        assert created.text == NEW_NOTE_TEXT
        assert created.slug == NEW_NOTE_SLUG
        assert created.author_id == self.author.id

        after = notes_state()
        assert len(after) == len(before) + 1

    def test_anonymous_user_cant_create_note(self):
        """Анонимного пользователя при POST отправляет на логин."""
        before = notes_state()

        response = self.client.post(NOTES_ADD_URL, data=CREATE_FORM_DATA)
        expected_url = f"{LOGIN_URL}?next={NOTES_ADD_URL}"
        self.assertRedirects(
            response, expected_url, fetch_redirect_response=False
        )

        after = notes_state()
        assert after == before

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        before = notes_state()

        data = CREATE_FORM_DATA.copy()
        data["slug"] = NOTE_SLUG
        response = self.author_client.post(NOTES_ADD_URL, data=data)

        form = response.context.get("form")
        self.assertFormError(form, "slug", NOTE_SLUG + WARNING)

        after = notes_state()
        assert after == before

    def test_empty_slug_generates_from_title(self):
        """Если slug пустой, он формируется автоматически из title."""
        before = notes_state()

        data = CREATE_FORM_DATA.copy()
        data.pop("slug")
        response = self.author_client.post(NOTES_ADD_URL, data=data)

        self.assertRedirects(
            response, NOTES_SUCCESS_URL, fetch_redirect_response=False
        )

        expected_slug = slugify(NEW_NOTE_TITLE)
        created = Note.objects.get(slug=expected_slug)
        assert created.title == NEW_NOTE_TITLE
        assert created.text == NEW_NOTE_TEXT
        assert created.slug == expected_slug
        assert created.author_id == self.author.id

        after = notes_state()
        assert len(after) == len(before) + 1

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        response = self.author_client.post(NOTES_EDIT_URL, data=EDIT_FORM_DATA)
        self.assertRedirects(
            response, NOTES_SUCCESS_URL, fetch_redirect_response=False
        )

        updated = Note.objects.get(pk=self.note.pk)
        assert updated.title == EDIT_FORM_DATA["title"]
        assert updated.text == EDIT_FORM_DATA["text"]
        assert updated.slug == EDIT_FORM_DATA["slug"]
        assert updated.author_id == self.author.id

    def test_reader_cant_edit_note(self):
        """Чужую заметку для другого пользователя не найти."""
        before = Note.objects.values("title", "text", "slug", "author_id").get(
            pk=self.note.pk
        )

        response = self.reader_client.post(NOTES_EDIT_URL, data=EDIT_FORM_DATA)
        assert response.status_code == HTTPStatus.NOT_FOUND

        after = Note.objects.values("title", "text", "slug", "author_id").get(
            pk=self.note.pk
        )
        assert after == before

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        response = self.author_client.post(NOTES_DELETE_URL)
        self.assertRedirects(
            response, NOTES_SUCCESS_URL, fetch_redirect_response=False
        )

        assert not Note.objects.filter(pk=self.note.pk).exists()

    def test_reader_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        before = Note.objects.values("title", "text", "slug", "author_id").get(
            pk=self.note.pk
        )

        response = self.reader_client.post(NOTES_DELETE_URL)
        assert response.status_code == HTTPStatus.NOT_FOUND

        after = Note.objects.values("title", "text", "slug", "author_id").get(
            pk=self.note.pk
        )
        assert after == before
