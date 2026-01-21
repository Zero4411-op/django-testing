"""Тут проверяем, чтобы страницы отдавали правильные данные в контекст."""

import pytest
from django.conf import settings

from news.forms import CommentForm

pytestmark = pytest.mark.django_db


def test_news_count(client, home_url, news_list):
    """На главной не должно быть больше лимита новостей."""
    assert (
        len(client.get(home_url).context["object_list"])
        == settings.NEWS_COUNT_ON_HOME_PAGE
    )


def test_news_order(client, home_url, news_list):
    """Самые свежие новости должны идти первыми."""
    dates = [item.date for item in client.get(home_url).context["object_list"]]
    assert dates == sorted(dates, reverse=True)


def test_comments_order(client, detail_url, comments):
    """Комментарии на странице должны идти от старых к новым."""
    news = client.get(detail_url).context["news"]
    created = [item.created for item in news.comment_set.all()]
    assert created == sorted(created)


def test_anonymous_client_has_no_form(client, detail_url):
    """Анониму форму комментирования не показываем."""
    assert "form" not in client.get(detail_url).context


def test_authorized_client_has_form(author_client, detail_url):
    """Залогиненному пользователю форму показываем."""
    assert isinstance(
        author_client.get(detail_url).context.get("form"),
        CommentForm,
    )
