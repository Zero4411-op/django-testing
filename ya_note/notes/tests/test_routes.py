"""Тесты маршрутов и прав доступа."""

from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note


class BaseNoteTestCase(TestCase):
    """База для тестов заметок: пользователи, клиенты и одна заметка."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт автора, читателя и одну заметку для проверок."""
        cls.author = cls._create_user(username="author")
        cls.reader = cls._create_user(username="reader")
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            slug="note-slug",
            author=cls.author,
        )

    @staticmethod
    def _create_user(username):
        """Создаёт пользователя по имени."""
        from django.contrib.auth import get_user_model

        return get_user_model().objects.create(username=username)

    def setUp(self):
        """Поднимает два клиента: автор и обычный пользователь."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)


class TestRoutes(BaseNoteTestCase):
    """Проверяет доступность страниц и редиректы."""

    def test_home_page_available_for_anonymous(self):
        """Главная страница открывается без авторизации."""
        url = reverse("notes:home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_auth_pages_available_for_anonymous(self):
        """Логин и регистрация открыты всем, а logout принимает POST."""
        for name in ("users:login", "users:signup"):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

        url = reverse("users:logout")
        response = self.client.post(url)
        self.assertIn(
            response.status_code,
            (HTTPStatus.OK, HTTPStatus.FOUND, HTTPStatus.SEE_OTHER),
        )

    def test_notes_pages_available_for_auth_user(self):
        """Авторизованный пользователь видит базовые страницы заметок."""
        for name in ("notes:list", "notes:add", "notes:success"):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_pages_available_for_author(self):
        """Автор видит свою заметку, просмотр, правка и удаление."""
        names = ("notes:detail", "notes:edit", "notes:delete")
        for name in names:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.author_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_note_pages_unavailable_for_other_user(self):
        """Чужая заметка для другого пользователя недоступна."""
        names = ("notes:detail", "notes:edit", "notes:delete")
        for name in names:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.reader_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_login_redirect_for_anonymous(self):
        """Анонимного пользователя отправляет на вход со всех страниц."""
        names = ("notes:list", "notes:add", "notes:success")
        for name in names:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                expected_url = f"{reverse('users:login')}?next={url}"
                self.assertRedirects(response, expected_url)

        names_with_slug = ("notes:detail", "notes:edit", "notes:delete")
        for name in names_with_slug:
            with self.subTest(name=name):
                url = reverse(name, args=(self.note.slug,))
                response = self.client.get(url)
                expected_url = f"{reverse('users:login')}?next={url}"
                self.assertRedirects(response, expected_url)
