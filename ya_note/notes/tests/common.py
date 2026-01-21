"""Общие константы и базовый класс для тестов заметок."""

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

NOTE_SLUG = "note-slug"

NOTES_HOME_URL = reverse("notes:home")
NOTES_LIST_URL = reverse("notes:list")
NOTES_ADD_URL = reverse("notes:add")
NOTES_SUCCESS_URL = reverse("notes:success")
NOTES_DETAIL_URL = reverse("notes:detail", args=(NOTE_SLUG,))
NOTES_EDIT_URL = reverse("notes:edit", args=(NOTE_SLUG,))
NOTES_DELETE_URL = reverse("notes:delete", args=(NOTE_SLUG,))

LOGIN_URL = reverse("users:login")
SIGNUP_URL = reverse("users:signup")
LOGOUT_URL = reverse("users:logout")

NOTES_LIST_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_LIST_URL}"
NOTES_ADD_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_ADD_URL}"
NOTES_SUCCESS_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_SUCCESS_URL}"
NOTES_DETAIL_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_DETAIL_URL}"
NOTES_EDIT_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_EDIT_URL}"
NOTES_DELETE_LOGIN_REDIRECT_URL = f"{LOGIN_URL}?next={NOTES_DELETE_URL}"


class BaseNoteTestCase(TestCase):
    """База для тестов заметок: пользователи, клиенты и одна заметка."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт автора, читателя и одну заметку для проверок."""
        cls.author = User.objects.create(username="author")
        cls.reader = User.objects.create(username="reader")

        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            slug=NOTE_SLUG,
            author=cls.author,
        )

        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.form_data = {
            "title": "New title",
            "text": "New text",
            "slug": "new-slug",
        }
