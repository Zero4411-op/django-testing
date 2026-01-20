"""Проверяем доступ к страницам, что открыто всем, а что только автору."""

import pytest

from news.forms import BAD_WORDS, WARNING
from news.models import Comment


pytestmark = pytest.mark.django_db

COMMENT_TEXT = "Текст комментария"
FORM_DATA = {"text": COMMENT_TEXT}


def comments_ids():
    return set(Comment.objects.values_list("id", flat=True))


def test_anonymous_user_cant_create_comment(client, detail_url):
    """Без логина комментарий не должен появиться в базе."""
    before = comments_ids()

    client.post(detail_url, data=FORM_DATA)

    assert comments_ids() == before


def test_user_can_create_comment(
    author_client,
    detail_url,
    comments_anchor_url,
    news,
    author,
):
    """Комментарий сохраняется, а потом идёт редирект к комментариям."""
    before = comments_ids()

    response = author_client.post(detail_url, data=FORM_DATA)
    assert response.status_code == 302
    assert response.url == comments_anchor_url

    after = comments_ids()
    new_id = (after - before).pop()
    created = Comment.objects.get(pk=new_id)

    assert created.text == COMMENT_TEXT
    assert created.news_id == news.id
    assert created.author_id == author.id


@pytest.mark.parametrize("bad_word", BAD_WORDS)
def test_user_cant_use_bad_words(author_client, detail_url, bad_word):
    """Запрещённые слова должны блокировать публикацию комментария."""
    before = comments_ids()

    bad_data = {"text": f"Какой-то текст, {bad_word}, еще текст"}
    response = author_client.post(detail_url, data=bad_data)

    form = response.context.get("form")
    assert form.errors["text"] == [WARNING]
    assert comments_ids() == before


def test_author_can_delete_comment(
    author_client,
    delete_url,
    comments_anchor_url,
    comment,
):
    """Автор удаляет комментарий и после запроса запись исчезает."""
    before = comments_ids()

    response = author_client.delete(delete_url)
    assert response.status_code == 302
    assert response.url == comments_anchor_url

    after = comments_ids()
    assert comment.id in before
    assert comment.id not in after


def test_reader_cant_delete_comment(reader_client, delete_url, comment):
    """Не автору отдаём 404 и не меняем состояние базы."""
    before = comments_ids()

    response = reader_client.delete(delete_url)
    assert response.status_code == 404
    assert comments_ids() == before


def test_author_can_edit_comment(
    author_client,
    edit_url,
    comments_anchor_url,
    comment,
):
    """Автор обновляет текст и в базе должен быть новый вариант."""
    new_text = "Обновлённый комментарий"
    response = author_client.post(edit_url, data={"text": new_text})

    assert response.status_code == 302
    assert response.url == comments_anchor_url

    updated = Comment.objects.get(pk=comment.pk)
    assert updated.text == new_text
    assert updated.author_id == comment.author_id
    assert updated.news_id == comment.news_id


def test_reader_cant_edit_comment(reader_client, edit_url, comment):
    """Чужой комментарий не редактируется и 404 и старый текст на месте."""
    before_text = Comment.objects.get(pk=comment.pk).text

    response = reader_client.post(edit_url, data={"text": "x"})
    assert response.status_code == 404

    after_text = Comment.objects.get(pk=comment.pk).text
    assert after_text == before_text
