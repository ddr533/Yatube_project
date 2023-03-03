from django.test import Client, TestCase
from django.urls import reverse


class TestAboutUrls(TestCase):
    def setUp(self) -> None:
        self.guest_client = Client()

    def test_urls_about(self):
        """Страницы /about/author/ и  /about/tech/ доступны пользователям"""
        urls = {
            '/about/author/': 200,
            '/about/tech/': 200,
        }
        for address, expected_status_code in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, expected_status_code)

    def test_urls_uses_correct_template(self):
        """Используются соответсвующие шаблоны для страниц приложения about"""
        templates_url_name = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html'
        }
        for address, template in templates_url_name.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)


class TestAboutPages(TestCase):

    def setUp(self):
        self.anon_user = Client()

    def test_pages_use_correct_templates(self):
        templates_page_names = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html'
        }
        for reverse_name, template in templates_page_names.items():
            response = self.anon_user.get(reverse_name)
            self.assertTemplateUsed(response, template)
