"""Тесты логики."""

from http import HTTPStatus

import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment

pytestmark = pytest.mark.django_db

FORM_DATA = {"text": "Текст комментария."}
EDIT_DATA = {"text": "Обновлённый текст комментария."}
READER_EDIT_DATA = {"text": "x"}

BAD_WORDS_DATA = [
    {"text": f"Какой-то текст, {bad_word}, еще текст"}
    for bad_word in BAD_WORDS
]


def test_anonymous_user_cant_create_comment(client, detail_url):
    """Без логина комментарий не должен появиться в базе."""
    client.post(detail_url, data=FORM_DATA)

    assert not Comment.objects.exists()


def test_user_can_create_comment(
    author_client,
    detail_url,
    comments_anchor_url,
    news,
    author,
):
    """Комментарий сохраняется, а потом идёт редирект к комментариям."""
    response = author_client.post(detail_url, data=FORM_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == comments_anchor_url

    assert Comment.objects.count() == 1
    created = Comment.objects.get()

    assert created.text == FORM_DATA["text"]
    assert created.news == news
    assert created.author == author


@pytest.mark.parametrize("bad_data", BAD_WORDS_DATA)
def test_user_cant_use_bad_words(author_client, detail_url, bad_data):
    """Запрещённые слова должны блокировать публикацию комментария."""
    response = author_client.post(detail_url, data=bad_data)

    form = response.context.get("form")
    assert form is not None
    assert form.errors["text"] == [WARNING]

    assert not Comment.objects.exists()


def test_author_can_delete_comment(
    author_client,
    delete_url,
    comments_anchor_url,
    comment,
):
    """Автор удаляет комментарий и после запроса запись исчезает."""
    response = author_client.delete(delete_url)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == comments_anchor_url

    assert not Comment.objects.exists()


def test_reader_cant_delete_comment(reader_client, delete_url, comment):
    """Не автору отдаём 404 и не меняем состояние базы."""
    response = reader_client.delete(delete_url)

    assert response.status_code == HTTPStatus.NOT_FOUND

    assert Comment.objects.count() == 1
    stored = Comment.objects.get(pk=comment.pk)
    assert stored.text == comment.text
    assert stored.news == comment.news
    assert stored.author == comment.author


def test_author_can_edit_comment(
    author_client,
    edit_url,
    comments_anchor_url,
    comment,
):
    """Автор обновляет текст и в базе должен быть новый вариант."""
    response = author_client.post(edit_url, data=EDIT_DATA)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == comments_anchor_url

    updated = Comment.objects.get(pk=comment.pk)
    assert updated.text == EDIT_DATA["text"]
    assert updated.news == comment.news
    assert updated.author == comment.author


def test_reader_cant_edit_comment(reader_client, edit_url, comment):
    """Чужой комментарий не редактируется и 404 и старый текст на месте."""
    before_text = comment.text
    before_news = comment.news
    before_author = comment.author

    response = reader_client.post(edit_url, data=READER_EDIT_DATA)

    assert response.status_code == HTTPStatus.NOT_FOUND

    reloaded = Comment.objects.get(pk=comment.pk)
    assert reloaded.text == before_text
    assert reloaded.news == before_news
    assert reloaded.author == before_author
