"""Тут проверяем, чтобы страницы отдавали правильные данные в контекст."""

from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News

User = get_user_model()


class TestHomePage(TestCase):
    """Сколько новостей показываем и в каком порядке."""

    HOME_URL = reverse("news:home")

    @classmethod
    def setUpTestData(cls):
        """Заранее создаём пачку новостей, чтобы было что сортировать."""
        now = timezone.now()
        all_news = [
            News(
                title=f"Новость {index}",
                text="Просто текст.",
                date=now - timedelta(days=index),
            )
            for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
        News.objects.bulk_create(all_news)

    def test_news_count(self):
        """На главной не должно быть больше лимита новостей."""
        response = self.client.get(self.HOME_URL)
        object_list = response.context["object_list"]
        self.assertEqual(object_list.count(), settings.NEWS_COUNT_ON_HOME_PAGE)

    def test_news_order(self):
        """Самые свежие новости должны идти первыми."""
        response = self.client.get(self.HOME_URL)
        object_list = response.context["object_list"]
        dates = [news.date for news in object_list]
        self.assertEqual(dates, sorted(dates, reverse=True))


class TestDetailPage(TestCase):
    """Порядок комментариев и видимость формы."""

    @classmethod
    def setUpTestData(cls):
        """Создаём новость так, чтобы легко проверить сортировку."""
        cls.news = News.objects.create(
            title="Тестовая новость", text="Просто текст."
        )
        cls.detail_url = reverse("news:detail", args=(cls.news.id,))
        cls.author = User.objects.create(username="Комментатор")

        now = timezone.now()
        for index in range(10):
            comment = Comment.objects.create(
                news=cls.news,
                author=cls.author,
                text=f"Текст {index}",
            )
            comment.created = now + timedelta(days=index)
            comment.save()

    def test_comments_order(self):
        """Комментарии на странице должны идти от старых к новым."""
        response = self.client.get(self.detail_url)
        self.assertIn("news", response.context)

        news = response.context["news"]
        comments = news.comment_set.all()
        created_list = [comment.created for comment in comments]
        self.assertEqual(created_list, sorted(created_list))

    def test_anonymous_client_has_no_form(self):
        """Анониму форму комментирования не показываем."""
        response = self.client.get(self.detail_url)
        self.assertNotIn("form", response.context)

    def test_authorized_client_has_form(self):
        """Залогиненному пользователю форму показываем."""
        self.client.force_login(self.author)
        response = self.client.get(self.detail_url)
        self.assertIn("form", response.context)
        self.assertIsInstance(response.context["form"], CommentForm)
