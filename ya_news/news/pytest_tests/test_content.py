"""Тут проверяем, чтобы страницы отдавали правильные данные в контекст."""

from datetime import timedelta

import pytest
from django.conf import settings
from django.utils import timezone

from news.forms import CommentForm
from news.models import News


pytestmark = pytest.mark.django_db


def test_news_count(client, home_url):
    """На главной не должно быть больше лимита новостей."""
    now = timezone.now()
    News.objects.bulk_create(
        [
            News(
                title=f"Новость {i}",
                text="Просто текст.",
                date=now - timedelta(days=i),
            )
            for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
    )

    news_items = list(client.get(home_url).context["object_list"])
    assert len(news_items) == settings.NEWS_COUNT_ON_HOME_PAGE


def test_news_order(client, home_url):
    """Самые свежие новости должны идти первыми."""
    now = timezone.now()
    News.objects.bulk_create(
        [
            News(
                title=f"Новость {i}",
                text="Просто текст.",
                date=now - timedelta(days=i),
            )
            for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
        ]
    )

    news_items = list(client.get(home_url).context["object_list"])
    dates = [item.date for item in news_items]
    assert dates == sorted(dates, reverse=True)


def test_comments_order(client, detail_url, ordered_comments):
    """Комментарии на странице должны идти от старых к новым."""
    response = client.get(detail_url)
    news = response.context["news"]

    comments = list(news.comment_set.all())
    created = [c.created for c in comments]
    assert created == sorted(created)


def test_anonymous_client_has_no_form(client, detail_url):
    """Анониму форму комментирования не показываем."""
    response = client.get(detail_url)
    assert "form" not in response.context


def test_authorized_client_has_form(author_client, detail_url):
    """Залогиненному пользователю форму показываем."""
    form = author_client.get(detail_url).context.get("form")
    assert isinstance(form, CommentForm)
