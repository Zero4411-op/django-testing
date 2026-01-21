"""Тесты логики."""

from http import HTTPStatus

from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note
from notes.tests.common import (
    BaseNoteTestCase,
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


def notes_ids():
    return set(Note.objects.values_list("pk", flat=True))


class TestNoteLogic(BaseNoteTestCase):
    """Проверки создания, slug-правил, редактирования и удаления заметок."""

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        before_ids = notes_ids()

        response = self.author_client.post(NOTES_ADD_URL, data=self.form_data)
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        new_ids = notes_ids() - before_ids
        self.assertEqual(len(new_ids), 1)
        created = Note.objects.get(pk=new_ids.pop())

        self.assertEqual(created.title, self.form_data["title"])
        self.assertEqual(created.text, self.form_data["text"])
        self.assertEqual(created.slug, self.form_data["slug"])
        self.assertEqual(created.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимного пользователя при POST отправляет на логин."""
        before = notes_state()

        response = self.client.post(NOTES_ADD_URL, data=self.form_data)
        self.assertRedirects(
            response,
            NOTES_ADD_LOGIN_REDIRECT_URL,
            fetch_redirect_response=False,
        )
        self.assertEqual(notes_state(), before)

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        before = notes_state()
        original_slug = self.form_data["slug"]

        self.form_data["slug"] = self.note.slug
        response = self.author_client.post(NOTES_ADD_URL, data=self.form_data)

        form = response.context.get("form")
        self.assertFormError(form, "slug", self.note.slug + WARNING)
        self.assertEqual(notes_state(), before)

        self.form_data["slug"] = original_slug

    def test_empty_slug_generates_from_title(self):
        """Если slug пустой, он формируется автоматически из title."""
        before_ids = notes_ids()
        original_slug = self.form_data.pop("slug")

        response = self.author_client.post(NOTES_ADD_URL, data=self.form_data)
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        new_ids = notes_ids() - before_ids
        self.assertEqual(len(new_ids), 1)
        created = Note.objects.get(pk=new_ids.pop())

        self.assertEqual(created.title, self.form_data["title"])
        self.assertEqual(created.text, self.form_data["text"])
        self.assertEqual(created.slug, slugify(self.form_data["title"]))
        self.assertEqual(created.author, self.author)

        self.form_data["slug"] = original_slug

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        before_data = self.form_data.copy()
        self.form_data.update(
            {
                "title": "Updated title",
                "text": "Updated text",
                "slug": "updated-slug",
            }
        )

        response = self.author_client.post(NOTES_EDIT_URL, data=self.form_data)
        self.assertRedirects(
            response,
            NOTES_SUCCESS_URL,
            fetch_redirect_response=False,
        )

        updated = Note.objects.get(pk=self.note.pk)
        self.assertEqual(updated.title, self.form_data["title"])
        self.assertEqual(updated.text, self.form_data["text"])
        self.assertEqual(updated.slug, self.form_data["slug"])
        self.assertEqual(updated.author, self.note.author)

        self.form_data.clear()
        self.form_data.update(before_data)

    def test_reader_cant_edit_note(self):
        """Чужую заметку для другого пользователя не найти."""
        before_data = self.form_data.copy()
        self.form_data.update(
            {
                "title": "Updated title",
                "text": "Updated text",
                "slug": "updated-slug",
            }
        )

        response = self.reader_client.post(NOTES_EDIT_URL, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        after = Note.objects.get(pk=self.note.pk)
        self.assertEqual(after.title, self.note.title)
        self.assertEqual(after.text, self.note.text)
        self.assertEqual(after.slug, self.note.slug)
        self.assertEqual(after.author, self.note.author)

        self.form_data.clear()
        self.form_data.update(before_data)

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
        response = self.reader_client.post(NOTES_DELETE_URL)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.assertTrue(Note.objects.filter(pk=self.note.pk).exists())

        after = Note.objects.get(pk=self.note.pk)
        self.assertEqual(after.title, self.note.title)
        self.assertEqual(after.text, self.note.text)
        self.assertEqual(after.slug, self.note.slug)
        self.assertEqual(after.author, self.note.author)
