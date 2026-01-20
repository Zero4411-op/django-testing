"""Общие константы и базовый класс для тестов."""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()

AUTHOR_USERNAME = "author"
READER_USERNAME = "reader"

NOTE_TITLE = "Заголовок"
NOTE_TEXT = "Текст"
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

PROTECTED_URLS = (
    NOTES_LIST_URL,
    NOTES_ADD_URL,
    NOTES_SUCCESS_URL,
    NOTES_DETAIL_URL,
    NOTES_EDIT_URL,
    NOTES_DELETE_URL,
)

LOGIN_REDIRECTS = tuple(
    (url, f"{LOGIN_URL}?next={url}") for url in PROTECTED_URLS
)

LOGOUT_ALLOWED_STATUSES = (
    HTTPStatus.OK,
    HTTPStatus.FOUND,
    HTTPStatus.SEE_OTHER,
)


class BaseNoteTestCase(TestCase):
    """База для тестов заметок, пользователи, клиенты и одна заметка."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт автора, читателя и одну заметку для проверок."""
        cls.author = User.objects.create(username=AUTHOR_USERNAME)
        cls.reader = User.objects.create(username=READER_USERNAME)
        cls.note = Note.objects.create(
            title=NOTE_TITLE,
            text=NOTE_TEXT,
            slug=NOTE_SLUG,
            author=cls.author,
        )

    def setUp(self):
        """Поднимает два клиента. Автор и обычный пользователь."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)
