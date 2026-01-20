"""Проверяем доступ к страницам, что открыто всем, а что только автору."""

import pytest
from pytest_django.asserts import assertRedirects


pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url_fixture",
    (
        "home_url",
        "detail_url",
        "login_url",
        "signup_url",
    ),
)
def test_public_pages_available_for_anonymous(request, client, url_fixture):
    """Страницы без ограничений должны открываться у анонимного клиента."""
    url = request.getfixturevalue(url_fixture)
    assert client.get(url).status_code == 200


@pytest.mark.parametrize(
    "client_fixture, expected_status",
    (("author_client", 200), ("reader_client", 404)),
)
@pytest.mark.parametrize("url_fixture", ("edit_url", "delete_url"))
def test_availability_for_comment_edit_and_delete(
    request,
    client_fixture,
    expected_status,
    url_fixture,
):
    """Редактирование и удаление доступны только автору комментария."""
    client = request.getfixturevalue(client_fixture)
    url = request.getfixturevalue(url_fixture)
    assert client.get(url).status_code == expected_status


@pytest.mark.parametrize("url_fixture", ("edit_url", "delete_url"))
def test_redirect_for_anonymous_client(
    request,
    client,
    login_url,
    url_fixture,
):
    """Гостя со всех закрытых страниц отправляет на страницу входа."""
    url = request.getfixturevalue(url_fixture)
    expected = f"{login_url}?next={url}"
    assertRedirects(client.get(url), expected)
