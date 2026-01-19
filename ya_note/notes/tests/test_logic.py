"""Тесты логики."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils.text import slugify

from notes.forms import WARNING
from notes.models import Note


class TestNoteCreation(TestCase):
    """Проверки создания заметок и правил для slug."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт пользователей, которых используем в тестах."""
        cls.author = cls._create_user(username="author")

    @staticmethod
    def _create_user(username: str):
        """Создаёт пользователя для тестов."""
        return get_user_model().objects.create(username=username)

    def setUp(self):
        """Готовит авторизованный клиент для автора."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

    @staticmethod
    def _form_data():
        """Возвращает валидные данные формы для создания заметки."""
        return {
            "title": "New title",
            "text": "New text",
            "slug": "new-slug",
        }

    def test_user_can_create_note(self):
        """Авторизованный пользователь может создать заметку."""
        url = reverse("notes:add")
        data = self._form_data()

        response = self.author_client.post(url, data=data)

        self.assertRedirects(
            response,
            reverse("notes:success"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Note.objects.count(), 1)

        created = Note.objects.get()
        self.assertEqual(created.title, data["title"])
        self.assertEqual(created.text, data["text"])
        self.assertEqual(created.slug, data["slug"])
        self.assertEqual(created.author, self.author)

    def test_anonymous_user_cant_create_note(self):
        """Анонимного пользователя при POST отправляет на логин."""
        url = reverse("notes:add")
        data = self._form_data()

        response = self.client.post(url, data=data)

        login_url = reverse("users:login")
        expected_url = f"{login_url}?next={url}"
        self.assertRedirects(
            response,
            expected_url,
            fetch_redirect_response=False,
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_not_unique_slug(self):
        """Нельзя создать две заметки с одинаковым slug."""
        existing = Note.objects.create(
            title="Existing",
            text="Text",
            slug="dup-slug",
            author=self.author,
        )
        url = reverse("notes:add")
        data = self._form_data()
        data["slug"] = existing.slug

        response = self.author_client.post(url, data=data)

        expected_error = existing.slug + WARNING
        form = response.context["form"]
        self.assertFormError(form, "slug", expected_error)
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug_generates_from_title(self):
        """Если slug пустой, он формируется автоматически из title."""
        url = reverse("notes:add")
        data = self._form_data()
        data.pop("slug")

        response = self.author_client.post(url, data=data)

        self.assertRedirects(
            response,
            reverse("notes:success"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Note.objects.count(), 1)

        created = Note.objects.get()
        self.assertEqual(created.slug, slugify(data["title"]))


class TestNoteEditDelete(TestCase):
    """Проверки редактирования и удаления заметок по правам доступа."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт пользователей и одну заметку автора."""
        cls.author = cls._create_user(username="author")
        cls.reader = cls._create_user(username="reader")
        cls.note = Note.objects.create(
            title="Old title",
            text="Old text",
            slug="note-slug",
            author=cls.author,
        )

    @staticmethod
    def _create_user(username: str):
        """Создаёт пользователя для тестов."""
        return get_user_model().objects.create(username=username)

    def setUp(self):
        """Готовит два клиента. Автора и другого пользователя."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    @staticmethod
    def _edit_data():
        """Возвращает новые данные для редактирования заметки."""
        return {
            "title": "Updated title",
            "text": "Updated text",
            "slug": "updated-slug",
        }

    def test_author_can_edit_note(self):
        """Автор может редактировать свою заметку."""
        url = reverse("notes:edit", args=(self.note.slug,))
        data = self._edit_data()

        response = self.author_client.post(url, data=data)

        self.assertRedirects(
            response,
            reverse("notes:success"),
            fetch_redirect_response=False,
        )
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, data["title"])
        self.assertEqual(self.note.text, data["text"])
        self.assertEqual(self.note.slug, data["slug"])

    def test_other_user_cant_edit_note(self):
        """Чужую заметку для другого пользователя не найти."""
        url = reverse("notes:edit", args=(self.note.slug,))
        data = self._edit_data()
        old = (self.note.title, self.note.text, self.note.slug)

        response = self.reader_client.post(url, data=data)

        self.assertEqual(response.status_code, 404)
        self.note.refresh_from_db()
        self.assertEqual(
            (self.note.title, self.note.text, self.note.slug), old
        )

    def test_author_can_delete_note(self):
        """Автор может удалить свою заметку."""
        url = reverse("notes:delete", args=(self.note.slug,))

        response = self.author_client.post(url)

        self.assertRedirects(
            response,
            reverse("notes:success"),
            fetch_redirect_response=False,
        )
        self.assertEqual(Note.objects.count(), 0)

    def test_other_user_cant_delete_note(self):
        """Другой пользователь не может удалить чужую заметку."""
        url = reverse("notes:delete", args=(self.note.slug,))

        response = self.reader_client.post(url)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Note.objects.count(), 1)
