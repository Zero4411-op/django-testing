"""Тесты контента, списки заметок и формы на страницах."""

from django.urls import reverse
from django.test import Client, TestCase

from notes.forms import NoteForm
from notes.models import Note


class TestContent(TestCase):
    """Проверяет, что страницы отдают ожидаемые данные в контексте."""

    @classmethod
    def setUpTestData(cls):
        """Создаёт пользователей и одну заметку автора."""
        from django.contrib.auth import get_user_model

        user_model = get_user_model()
        cls.author = user_model.objects.create(username="author")
        cls.reader = user_model.objects.create(username="reader")
        cls.note = Note.objects.create(
            title="Заголовок",
            text="Текст",
            slug="note-slug",
            author=cls.author,
        )

    def setUp(self):
        """Создаём два клиента, для автора и для другого пользователя."""
        self.author_client = Client()
        self.author_client.force_login(self.author)

        self.reader_client = Client()
        self.reader_client.force_login(self.reader)

    def test_note_visible_in_list_for_author(self):
        """Автор видит свою заметку в списке."""
        url = reverse("notes:list")
        response = self.author_client.get(url)
        object_list = response.context["object_list"]
        self.assertIn(self.note, object_list)

    def test_note_hidden_in_list_for_other_user(self):
        """Чужие заметки не попадают в список другого пользователя."""
        url = reverse("notes:list")
        response = self.reader_client.get(url)
        object_list = response.context["object_list"]
        self.assertNotIn(self.note, object_list)

    def test_create_page_has_form(self):
        """На странице создания заметки есть форма."""
        url = reverse("notes:add")
        response = self.author_client.get(url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)

    def test_edit_page_has_form(self):
        """На странице редактирования заметки есть форма."""
        url = reverse("notes:edit", args=(self.note.slug,))
        response = self.author_client.get(url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], NoteForm)
