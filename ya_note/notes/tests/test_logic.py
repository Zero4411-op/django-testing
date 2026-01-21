"""Тесты логики."""

from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.common import (
    BaseNoteTestCase,
    NOTE_SLUG,
    NOTES_ADD_LOGIN_REDIRECT_URL,
    NOTES_ADD_URL,
    NOTES_DELETE_URL,
    NOTES_EDIT_URL,
    NOTES_SUCCESS_URL,
)


def notes_state():
    """Содержимое таблицы заметок для сравнения до и после."""
    return set(
        Note.objects.values_list(
            "title",
            "text",
            "slug",
            "author_id",
        )
    )


class TestNoteLogic(BaseNoteTestCase):
    """Проверки создания, slug-правил, редактирования и удаления заметок."""

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        before = notes_state()

        response = self.author_client.post(
            NOTES_ADD_URL,
            data=self.create_form_data,
        )
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        created_qs = Note.objects.exclude(pk=self.note.pk)
        self.assertEqual(created_qs.count(), 1)
        created = created_qs.get()

        self.assertEqual(created.title, self.create_form_data["title"])
        self.assertEqual(created.text, self.create_form_data["text"])
        self.assertEqual(created.slug, self.create_form_data["slug"])
        self.assertEqual(created.author, self.author)

        expected_after = before | {
            (
                self.create_form_data["title"],
                self.create_form_data["text"],
                self.create_form_data["slug"],
                self.author.pk,
            )
        }
        self.assertEqual(notes_state(), expected_after)

    def test_anonymous_user_cant_create_note(self):
        """Анонимного пользователя при POST отправляет на логин."""
        before = notes_state()

        response = self.client.post(
            NOTES_ADD_URL,
            data=self.create_form_data,
        )
        self.assertRedirects(
            response,
            NOTES_ADD_LOGIN_REDIRECT_URL,
            fetch_redirect_response=False,
        )
        self.assertEqual(notes_state(), before)

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        before = notes_state()

        data = {**self.create_form_data, "slug": NOTE_SLUG}
        response = self.author_client.post(NOTES_ADD_URL, data=data)

        form = response.context.get("form")
        self.assertFormError(form, "slug", NOTE_SLUG + WARNING)
        self.assertEqual(notes_state(), before)

    def test_empty_slug_generates_from_title(self):
        """Если slug пустой, он формируется автоматически из title."""
        before = notes_state()

        data = {
            "title": self.create_form_data["title"],
            "text": self.create_form_data["text"],
        }
        response = self.author_client.post(NOTES_ADD_URL, data=data)

        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        created_qs = Note.objects.exclude(pk=self.note.pk)
        self.assertEqual(created_qs.count(), 1)
        created = created_qs.get()

        expected_slug = slugify(data["title"])
        self.assertEqual(created.title, data["title"])
        self.assertEqual(created.text, data["text"])
        self.assertEqual(created.slug, expected_slug)
        self.assertEqual(created.author, self.author)

        expected_after = before | {
            (data["title"], data["text"], expected_slug, self.author.pk)
        }
        self.assertEqual(notes_state(), expected_after)

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        response = self.author_client.post(
            NOTES_EDIT_URL,
            data=self.edit_form_data,
        )
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        updated = Note.objects.get(pk=self.note.pk)
        self.assertEqual(updated.title, self.edit_form_data["title"])
        self.assertEqual(updated.text, self.edit_form_data["text"])
        self.assertEqual(updated.slug, self.edit_form_data["slug"])
        self.assertEqual(updated.author, self.author)

    def test_reader_cant_edit_note(self):
        """Чужую заметку для другого пользователя не найти."""
        before_title = self.note.title
        before_text = self.note.text
        before_slug = self.note.slug
        before_author = self.note.author

        response = self.reader_client.post(
            NOTES_EDIT_URL,
            data=self.edit_form_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        after = Note.objects.get(pk=self.note.pk)
        self.assertEqual(after.title, before_title)
        self.assertEqual(after.text, before_text)
        self.assertEqual(after.slug, before_slug)
        self.assertEqual(after.author, before_author)

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        before_count = Note.objects.count()

        response = self.author_client.post(NOTES_DELETE_URL)
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        self.assertEqual(Note.objects.count(), before_count - 1)
        self.assertFalse(Note.objects.filter(pk=self.note.pk).exists())

    def test_reader_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        before_title = self.note.title
        before_text = self.note.text
        before_slug = self.note.slug
        before_author = self.note.author
        before_count = Note.objects.count()

        response = self.reader_client.post(NOTES_DELETE_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())
        self.assertEqual(Note.objects.count(), before_count)

        after = Note.objects.get(pk=self.note.pk)
        self.assertEqual(after.title, before_title)
        self.assertEqual(after.text, before_text)
        self.assertEqual(after.slug, before_slug)
        self.assertEqual(after.author, before_author)
