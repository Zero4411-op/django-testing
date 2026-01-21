"""Тесты маршрутов и прав доступа."""

from http import HTTPStatus

from notes.tests.common import (
    BaseNoteTestCase,
    LOGIN_URL,
    LOGOUT_URL,
    NOTES_ADD_LOGIN_REDIRECT_URL,
    NOTES_ADD_URL,
    NOTES_DELETE_LOGIN_REDIRECT_URL,
    NOTES_DELETE_URL,
    NOTES_DETAIL_LOGIN_REDIRECT_URL,
    NOTES_DETAIL_URL,
    NOTES_EDIT_LOGIN_REDIRECT_URL,
    NOTES_EDIT_URL,
    NOTES_HOME_URL,
    NOTES_LIST_LOGIN_REDIRECT_URL,
    NOTES_LIST_URL,
    NOTES_SUCCESS_LOGIN_REDIRECT_URL,
    NOTES_SUCCESS_URL,
    SIGNUP_URL,
)


class TestRoutes(BaseNoteTestCase):
    """Проверяет доступность страниц и редиректы."""

    def test_status_codes(self):
        """Проверяем коды ответов для разных пользователей и страниц."""
        ok = HTTPStatus.OK
        found = HTTPStatus.FOUND
        not_found = HTTPStatus.NOT_FOUND

        cases = [
            (self.client.get, NOTES_HOME_URL, ok),
            (self.client.get, LOGIN_URL, ok),
            (self.client.get, SIGNUP_URL, ok),
            (self.author_client.get, NOTES_LIST_URL, ok),
            (self.author_client.get, NOTES_ADD_URL, ok),
            (self.author_client.get, NOTES_SUCCESS_URL, ok),
            (self.author_client.get, NOTES_DETAIL_URL, ok),
            (self.author_client.get, NOTES_EDIT_URL, ok),
            (self.author_client.get, NOTES_DELETE_URL, ok),
            (self.reader_client.get, NOTES_DETAIL_URL, not_found),
            (self.reader_client.get, NOTES_EDIT_URL, not_found),
            (self.reader_client.get, NOTES_DELETE_URL, not_found),
            (self.client.get, NOTES_LIST_URL, found),
            (self.client.get, NOTES_ADD_URL, found),
            (self.client.get, NOTES_SUCCESS_URL, found),
            (self.client.get, NOTES_DETAIL_URL, found),
            (self.client.get, NOTES_EDIT_URL, found),
            (self.client.get, NOTES_DELETE_URL, found),
            (self.client.post, LOGOUT_URL, ok),
        ]

        for method, url, expected in cases:
            with self.subTest(url=url):
                self.assertEqual(method(url).status_code, expected)

    def test_redirects_for_anonymous(self):
        """Анонимного пользователя отправляет на вход с закрытых страниц."""
        cases = [
            (NOTES_LIST_URL, NOTES_LIST_LOGIN_REDIRECT_URL),
            (NOTES_ADD_URL, NOTES_ADD_LOGIN_REDIRECT_URL),
            (NOTES_SUCCESS_URL, NOTES_SUCCESS_LOGIN_REDIRECT_URL),
            (NOTES_DETAIL_URL, NOTES_DETAIL_LOGIN_REDIRECT_URL),
            (NOTES_EDIT_URL, NOTES_EDIT_LOGIN_REDIRECT_URL),
            (NOTES_DELETE_URL, NOTES_DELETE_LOGIN_REDIRECT_URL),
        ]

        for url, expected in cases:
            with self.subTest(url=url):
                self.assertRedirects(self.client.get(url), expected)
