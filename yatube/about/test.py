from http import HTTPStatus

from django.test import Client, TestCase


class TestAboutUrls(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_urls_about(self):
        """Страницы /about/author/ и  /about/tech/ доступны пользователям."""
        urls = {
            '/about/author/': HTTPStatus.OK,
            '/about/tech/': HTTPStatus.OK,
        }
        for address, expected_status_code in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, expected_status_code)

    def test_urls_uses_correct_template(self):
        """Используются соответсвующие шаблоны для страниц приложения about."""
        templates_url_name = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in templates_url_name.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)
