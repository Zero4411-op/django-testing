from datetime import timedelta

import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from news.models import Comment, News


@pytest.fixture()
def author(django_user_model):
    return django_user_model.objects.create(username="Комментатор")


@pytest.fixture()
def reader(django_user_model):
    return django_user_model.objects.create(username="Читатель")


@pytest.fixture()
def author_client(author):
    client = Client()
    client.force_login(author)
    return client


@pytest.fixture()
def reader_client(reader):
    client = Client()
    client.force_login(reader)
    return client


@pytest.fixture()
def home_url():
    return reverse("news:home")


@pytest.fixture()
def login_url():
    return reverse("users:login")


@pytest.fixture()
def signup_url():
    return reverse("users:signup")


@pytest.fixture()
def news():
    return News.objects.create(
        title="Тестовая новость",
        text="Просто текст.",
    )


@pytest.fixture()
def detail_url(news):
    return reverse("news:detail", args=(news.pk,))


@pytest.fixture()
def comments_anchor_url(detail_url):
    return f"{detail_url}#comments"


@pytest.fixture()
def comment(news, author):
    return Comment.objects.create(
        news=news,
        author=author,
        text="Текст комментария",
    )


@pytest.fixture()
def edit_url(comment):
    return reverse("news:edit", args=(comment.pk,))


@pytest.fixture()
def delete_url(comment):
    return reverse("news:delete", args=(comment.pk,))


@pytest.fixture()
def edit_redirect_url(login_url, edit_url):
    return f"{login_url}?next={edit_url}"


@pytest.fixture()
def delete_redirect_url(login_url, delete_url):
    return f"{login_url}?next={delete_url}"


@pytest.fixture()
def comments(news, author):
    now = timezone.now()
    for i in range(10):
        created = Comment.objects.create(
            news=news,
            author=author,
            text=f"Текст {i}",
        )
        Comment.objects.filter(pk=created.pk).update(
            created=now + timedelta(days=i)
        )


@pytest.fixture()
def news_list():
    now = timezone.now()
    News.objects.bulk_create(
        News(
            title=f"Новость {i}",
            text="Просто текст.",
            date=now - timedelta(days=i),
        )
        for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    )
