"""Тесты маршрутов и прав доступа."""

from http import HTTPStatus

from notes.tests.common import (
    BaseNoteTestCase,
    LOGIN_REDIRECTS,
    LOGIN_URL,
    LOGOUT_ALLOWED_STATUSES,
    LOGOUT_URL,
    NOTES_ADD_URL,
    NOTES_DELETE_URL,
    NOTES_DETAIL_URL,
    NOTES_EDIT_URL,
    NOTES_HOME_URL,
    NOTES_LIST_URL,
    NOTES_SUCCESS_URL,
    SIGNUP_URL,
)


class TestRoutes(BaseNoteTestCase):
    """Проверяет доступность страниц и редиректы."""

    def test_status_codes(self):
        """Проверяем коды ответов для разных пользователей и страниц."""
        cases = [
            (NOTES_HOME_URL, self.client, HTTPStatus.OK),
            (LOGIN_URL, self.client, HTTPStatus.OK),
            (SIGNUP_URL, self.client, HTTPStatus.OK),
            (NOTES_LIST_URL, self.author_client, HTTPStatus.OK),
            (NOTES_ADD_URL, self.author_client, HTTPStatus.OK),
            (NOTES_SUCCESS_URL, self.author_client, HTTPStatus.OK),
            (NOTES_DETAIL_URL, self.author_client, HTTPStatus.OK),
            (NOTES_EDIT_URL, self.author_client, HTTPStatus.OK),
            (NOTES_DELETE_URL, self.author_client, HTTPStatus.OK),
            (NOTES_DETAIL_URL, self.reader_client, HTTPStatus.NOT_FOUND),
            (NOTES_EDIT_URL, self.reader_client, HTTPStatus.NOT_FOUND),
            (NOTES_DELETE_URL, self.reader_client, HTTPStatus.NOT_FOUND),
            (NOTES_LIST_URL, self.client, HTTPStatus.FOUND),
            (NOTES_ADD_URL, self.client, HTTPStatus.FOUND),
            (NOTES_SUCCESS_URL, self.client, HTTPStatus.FOUND),
            (NOTES_DETAIL_URL, self.client, HTTPStatus.FOUND),
            (NOTES_EDIT_URL, self.client, HTTPStatus.FOUND),
            (NOTES_DELETE_URL, self.client, HTTPStatus.FOUND),
        ]

        for url, client, status in cases:
            with self.subTest(url=url, status=status):
                assert client.get(url).status_code == status

        assert (
            self.client.post(LOGOUT_URL).status_code in LOGOUT_ALLOWED_STATUSES
        )

    def test_redirects_for_anonymous(self):
        """Анонимного пользователя отправляет на вход с закрытых страниц."""
        for url, expected in LOGIN_REDIRECTS:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), expected)
