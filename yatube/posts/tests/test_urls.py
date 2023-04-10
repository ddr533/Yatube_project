from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class TestPostsURLs(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.not_author = User.objects.create_user(username='not_author')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        Post.objects.create(
            author=cls.author,
            text='test_post' * 10,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.auth_author = Client()
        self.auth_not_author = Client()
        self.auth_author.force_login(self.author)
        self.auth_not_author.force_login(self.not_author)
        cache.clear()

    def test_urls_availability_for_guest_client(self):
        """
        Проверка доступности страниц для всех типов пользователей.

        Запрос к несуществующей странице возвращает код 404.
        """
        users = (self.auth_author, self.guest_client, self.auth_not_author)
        urls_for_guest_clients = {
            '/': HTTPStatus.OK,
            '/group/test_slug/': HTTPStatus.OK,
            '/profile/author/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/search/': HTTPStatus.OK,
            '/search/?text=test/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for user in users:
            for url, expected_status_code in urls_for_guest_clients.items():
                with self.subTest(url=url):
                    response = user.get(url)
                    self.assertEqual(response.status_code,
                                     expected_status_code)

    def test_create_page_availability_for_auth_user(self):
        """
        Тестирование доступности страниц авторизованному пользователю.

        Страница для создания записи и страница с подписками доступна
        авторизованному пользователю.
        """
        response = self.auth_not_author.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.auth_not_author.get('/follow/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_url_availability_for_author(self):
        """Страница редактирования записи доступна автору записи."""
        response = self.auth_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_quest_client(self):
        """
        Тестирование редиректов для неавторизованных пользователей.

        Перенаправление неавторизованных пользователей со страницы создания,
        редактирования, комментирования и удаления записей
        на страницу авторизации.
        """
        urls_for_redirect_guest_clients = (
            '/create/',
            '/posts/1/edit/',
            '/posts/1/delete/',
            '/posts/1/comment/'
        )
        for address in urls_for_redirect_guest_clients:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response,
                                     (f'/auth/login/?next={address}'))

    def test_pages_not_avaliable_for_non_author(self):
        """
        Тестирование доступности страниц для не авторов записей.

        Страница по адресу posts/<id>/edit/ и posts/<id>/delete/
        вызовет ошибку PermissionDenied() при запросе от пользователя, не
        являющего автором.
        """
        urls_for_redirect_non_author = (
            '/posts/1/edit/',
            '/posts/1/delete/',
        )
        for address in urls_for_redirect_non_author:
            with self.subTest(address=address):
                response = self.auth_not_author.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_url_availability_for_author(self):
        """
        Тестирование редиректа при удалении записи.

        Страница по адресу /posts/<post_id>/delete/ перенаправит автора
        записи на страницу его профиля.
        """
        response = self.auth_author.get('/posts/1/delete/', follow=True)
        self.assertRedirects(response, '/profile/author/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test_slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/search/?text=test/': 'posts/index.html',
            '/follow/': 'posts/follow.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.auth_author.get(address)
                self.assertTemplateUsed(response, template)
