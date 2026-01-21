"""Проверяем доступ к страницам, что открыто всем, а что только автору."""

from http import HTTPStatus

import pytest
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db

ANON_CLIENT = pytest.lazy_fixture("client")
AUTHOR_CLIENT = pytest.lazy_fixture("author_client")
READER_CLIENT = pytest.lazy_fixture("reader_client")

HOME_URL = pytest.lazy_fixture("home_url")
DETAIL_URL = pytest.lazy_fixture("detail_url")
LOGIN_URL = pytest.lazy_fixture("login_url")
SIGNUP_URL = pytest.lazy_fixture("signup_url")

EDIT_URL = pytest.lazy_fixture("edit_url")
DELETE_URL = pytest.lazy_fixture("delete_url")

EDIT_REDIRECT_URL = pytest.lazy_fixture("edit_redirect_url")
DELETE_REDIRECT_URL = pytest.lazy_fixture("delete_redirect_url")


@pytest.mark.parametrize(
    "client_obj, url, expected_status",
    (
        (ANON_CLIENT, HOME_URL, HTTPStatus.OK),
        (ANON_CLIENT, DETAIL_URL, HTTPStatus.OK),
        (ANON_CLIENT, LOGIN_URL, HTTPStatus.OK),
        (ANON_CLIENT, SIGNUP_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, EDIT_URL, HTTPStatus.OK),
        (AUTHOR_CLIENT, DELETE_URL, HTTPStatus.OK),
        (READER_CLIENT, EDIT_URL, HTTPStatus.NOT_FOUND),
        (READER_CLIENT, DELETE_URL, HTTPStatus.NOT_FOUND),
        (ANON_CLIENT, EDIT_URL, HTTPStatus.FOUND),
        (ANON_CLIENT, DELETE_URL, HTTPStatus.FOUND),
    ),
)
def test_status_codes(client_obj, url, expected_status):
    """Все проверки status_code — в одном тесте."""
    assert client_obj.get(url).status_code == expected_status


@pytest.mark.parametrize(
    "url, expected",
    (
        (EDIT_URL, EDIT_REDIRECT_URL),
        (DELETE_URL, DELETE_REDIRECT_URL),
    ),
)
def test_redirect_for_anonymous_client(client, url, expected):
    """Гостя со всех закрытых страниц отправляет на страницу входа."""
    assertRedirects(client.get(url), expected)
