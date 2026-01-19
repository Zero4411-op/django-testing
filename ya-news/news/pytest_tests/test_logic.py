"""Проверяем доступ к страницам, что открыто всем, а что только автору."""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

User = get_user_model()


class TestCommentCreation(TestCase):
    """Пишем комментарии, а заодно ловим запреты и ошибки формы."""

    COMMENT_TEXT = "Текст комментария"

    @classmethod
    def setUpTestData(cls):
        """Готовим новость и пользователя, чтобы не повторяться в тестах."""
        cls.news = News.objects.create(title="Заголовок", text="Текст")
        cls.url = reverse("news:detail", args=(cls.news.id,))
        cls.user = User.objects.create(username="Мимо Крокодил")

        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)

        cls.form_data = {"text": cls.COMMENT_TEXT}

    def test_anonymous_user_cant_create_comment(self):
        """Без логина комментарий не должен появиться в базе."""
        self.client.post(self.url, data=self.form_data)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_can_create_comment(self):
        """Комментарий сохраняется, а потом идёт редирект к комментариям."""
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertRedirects(response, f"{self.url}#comments")

        self.assertEqual(Comment.objects.count(), 1)
        comment = Comment.objects.get()

        self.assertEqual(comment.text, self.COMMENT_TEXT)
        self.assertEqual(comment.news, self.news)
        self.assertEqual(comment.author, self.user)

    def test_user_cant_use_bad_words(self):
        """Запрещённые слова должны блокировать публикацию комментария."""
        bad_text = f"Какой-то текст, {BAD_WORDS[0]}, еще текст"
        response = self.auth_client.post(self.url, data={"text": bad_text})

        form = response.context["form"]
        self.assertFormError(form=form, field="text", errors=WARNING)
        self.assertEqual(Comment.objects.count(), 0)


class TestCommentEditDelete(TestCase):
    """Чужие комментарии не трогаем, свои можно менять и удалять."""

    COMMENT_TEXT = "Текст комментария"
    NEW_COMMENT_TEXT = "Обновлённый комментарий"

    @classmethod
    def setUpTestData(cls):
        """Создаём автора, читателя и один комментарий для проверок прав."""
        cls.news = News.objects.create(title="Заголовок", text="Текст")
        news_url = reverse("news:detail", args=(cls.news.id,))
        cls.url_to_comments = f"{news_url}#comments"

        cls.author = User.objects.create(username="Автор комментария")
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.reader = User.objects.create(username="Читатель")
        cls.reader_client = Client()
        cls.reader_client.force_login(cls.reader)

        cls.comment = Comment.objects.create(
            news=cls.news,
            author=cls.author,
            text=cls.COMMENT_TEXT,
        )
        cls.edit_url = reverse("news:edit", args=(cls.comment.id,))
        cls.delete_url = reverse("news:delete", args=(cls.comment.id,))
        cls.form_data = {"text": cls.NEW_COMMENT_TEXT}

    def test_author_can_delete_comment(self):
        """Автор удаляет комментарий и после запроса запись исчезает."""
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.url_to_comments)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), 0)

    def test_user_cant_delete_comment_of_another_user(self):
        """Не автору отдаём 404 и не меняем состояние базы."""
        response = self.reader_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Comment.objects.count(), 1)

    def test_author_can_edit_comment(self):
        """Автор обновляет текст и в базе должен быть новый вариант."""
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.url_to_comments)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.NEW_COMMENT_TEXT)

    def test_user_cant_edit_comment_of_another_user(self):
        """Чужой комментарий не редактируется и 404 и старый текст на месте."""
        response = self.reader_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

        self.comment.refresh_from_db()
        self.assertEqual(self.comment.text, self.COMMENT_TEXT)
