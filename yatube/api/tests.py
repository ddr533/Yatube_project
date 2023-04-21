from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from rest_framework import status

from posts.models import Group


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

    def setUp(self):
        self.user_client = APIClient()
        self.anon_client = APIClient()
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(self.admin)
        self.user_client.force_authenticate(self.user)


    def test_user_access_to_group_list_and_detail(self):
        """Пользователи могут осуществлять GET запросы к модели Group."""
        users = (self.anon_client, self.user_client)
        urls = (
            (reverse('api:group-list'), status.HTTP_200_OK),
            (reverse('api:group-detail', kwargs={'pk': self.group.id}),
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
        response = self.admin_client.delete(reverse('api:group-detail',
                                                    kwargs={'pk': 2}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.user_client.post(reverse('api:group-list'), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.user_client.put(
            reverse('api:group-detail', kwargs={'pk': 2}), data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        response = self.user_client.delete(reverse('api:group-detail',
                                                    kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)