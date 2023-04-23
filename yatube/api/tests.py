from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status

from posts.models import Group, Post, Comment, Follow


User = get_user_model()


class TestMyAPI(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = User.objects.create_superuser(
            username='admin',
            password='password',
            email='admin@example.com'
        )
        cls.user = User.objects.create_user(
            username='user',
            password='password',
            email='user@example.com'
        )

        cls.group = Group.objects.create(
            title='test_group',
            description='description',
            slug='slug'
        )
        cls.post = Post.objects.create(text='post', author=cls.user)
        cls.comment = Comment.objects.create(text='comment',
                                             post=cls.post,
                                             author=cls.user)
        cls.follow = Follow.objects.create(user=cls.user, author=cls.admin)

    def setUp(self):
        self.user_client = APIClient()
        self.anon_client = APIClient()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)
        self.user_client.force_authenticate(self.user)


    def test_user_access_to_group_list_and_detail(self):
        """Проверка GET запросов к ресурсам от анонимных и аутентифицированных
        пользователей."""
        users = (self.anon_client, self.user_client)
        urls = (
            (reverse('api:group-list'), status.HTTP_200_OK),
            (reverse('api:group-detail', kwargs={'pk': self.group.id}),
             status.HTTP_200_OK),
            (reverse('api:post-list'), status.HTTP_200_OK),
            (reverse('api:post-detail', kwargs={'pk': self.post.id}),
            status.HTTP_200_OK),
            (reverse('api:comment-list', kwargs={'post_id': self.post.id}),
             status.HTTP_200_OK),
            (reverse('api:comment-detail',
                     kwargs={'post_id': self.post.id, 'pk': self.comment.id}),
             status.HTTP_200_OK),
        )
        for user in users:
            for url, expected_status_code in urls:
                with self.subTest(url=url, status_code=expected_status_code):
                    response = user.get(url)
                    self.assertEqual(response.status_code, expected_status_code)

    def test_insecure_request_for_group(self):
        """Создавать, изменять и удалять группу может только администратор."""
        data = {
            'title': 'test_group_1',
            'description': 'description_1',
            'slug': 'slug_1',
        }
        response = self.admin_client.post(reverse('api:group-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.admin_client.put(
            reverse('api:group-detail', kwargs={'pk': 2}), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.admin_client.delete(
            reverse('api:group-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.user_client.post(reverse('api:group-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user_client.put(
            reverse('api:group-detail', kwargs={'pk': 2}), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user_client.delete(
            reverse('api:group-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_insecure_request_for_post(self):
        """Создавать запись может только аутентифицированный пользователь.
        Изменять запись может только автор."""
        data = {
            'text': 'test_1',
            'group': self.group.id,
        }
        response = self.user_client.post(reverse('api:post-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.user_client.put(
            reverse('api:post-detail', kwargs={'pk': 2}), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.admin_client.put(
            reverse('api:post-detail', kwargs={'pk': 2}), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.admin_client.delete(
            reverse('api:post-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user_client.delete(
            reverse('api:post-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.anon_client.post(reverse('api:post-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_insecure_request_for_comment(self):
        """Комментировать может только аутентифицированный пользователь.
         Изменять комментарии может только автор."""
        data = {
            'text': 'comment_1',
        }
        response = self.user_client.post(
            reverse('api:comment-list',
                    kwargs={'post_id': self.post.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.user_client.put(
            reverse('api:comment-detail',
                    kwargs={'post_id': self.post.id, 'pk': 1}), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.admin_client.put(
            reverse('api:comment-detail',
                    kwargs={'post_id': self.post.id, 'pk': 1}), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.admin_client.delete(
            reverse('api:comment-detail',
                    kwargs={'post_id': self.post.id, 'pk': 1}), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        response = self.user_client.delete(
            reverse('api:comment-detail',
                    kwargs={'post_id': self.post.id, 'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.anon_client.post(
            reverse('api:comment-list',
                    kwargs={'post_id': self.post.id}), data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_for_follow(self):
        """Получить список подписок и подписаться могут только
        аутентифицированные пользователи. Удалить подписку может
        только подписчик."""
        response = self.anon_client.get(reverse('api:follow-list'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.user_client.get(reverse('api:follow-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.anon_client.post(
            reverse('api:follow-list'), data={'author': self.user})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        response = self.admin_client.post(
            reverse('api:follow-list'), data={'author': self.user.username})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        #Пытаемся удалить чужую подписку
        response = self.admin_client.delete(
            reverse('api:follow-detail', kwargs={'pk': self.follow.id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        #Удаляем свою подписку
        response = self.admin_client.delete(
            reverse('api:follow-detail', kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_put_patch_method_not_allow_for_follow(self):
        """Методы PUT и PATCH не доступны пользователям
        для работы с подписками."""
        response = self.user_client.put(
            reverse('api:follow-detail', kwargs={'pk': self.follow.id}),
            data = {'author': 'test'})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.user_client.patch(
            reverse('api:follow-detail', kwargs={'pk': self.follow.id}),
            data={'author': 'test'})
        self.assertEqual(response.status_code,
                         status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_user_cant_follow_itself(self):
        """Нельзя подписаться на самого себя."""
        response = self.user_client.post(
            reverse('api:follow-list'), data={'author': self.user})
        self.assertEqual(response.status_code,
                                 status.HTTP_400_BAD_REQUEST)

    def test_user_cant_duplicate_follow(self):
        """Нельзя оформлять дубликат подписки."""
        response = self.user_client.post(
            reverse('api:follow-list'), data={'author': self.admin})
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST)


