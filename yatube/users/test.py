from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .models import UserProfile


User = get_user_model()


class TestUserUrls(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user',
                                             password='test@12345')
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

    def test_urls_status_code_for_auth_user(self):
        """Пользовательские служебные страницы имеют
         правильные response коды.
         """
        pages_code = {
            reverse('users:password_change'): HTTPStatus.OK,
            reverse('users:set_user_info'): HTTPStatus.OK,
            reverse('users:signup'): HTTPStatus.OK,
            reverse('users:login'): HTTPStatus.OK,
            reverse('users:logout'): HTTPStatus.OK,
            reverse('users:password_reset_form'): HTTPStatus.OK,

        }
        for page, status_code in pages_code.items():
            with self.subTest(page=page):
                responce = self.auth_user.get(page)
                self.assertEqual(responce.status_code, status_code)


class TestUserPages(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user',
                                             password='test@12345')
        self.auth_user = Client()
        self.auth_user.force_login(self.user)
        self.anon_user = Client()

    def test_pages_use_correct_templates(self):
        """Пользовательские служебные страницы используют правильные шаблоны."""
        self.uidb64 = 'MTA'
        self.token = 'a88hdr-5fb0f72acbe1e9d2b81b7810dee31037'
        templates_page_names = {
            reverse('users:signup'): 'users/signup.html',
            reverse('users:login'): 'users/login.html',
            reverse('users:password_reset_form'):
                'users/password_reset_form.html',
            reverse('users:password_reset_done'):
                'users/password_reset_done.html',
            reverse('users:password_reset_confirm',
                    kwargs={'uidb64': self.uidb64, 'token': self.token}):
                'users/password_reset_confirm.html',
            reverse('users:password_reset_comlete'):
                'users/password_reset_complete.html',
            reverse('users:password_change'):
                'users/password_change_form.html',
            reverse('users:password_change_done'):
                'users/password_change_done.html',
            reverse('users:set_user_info'): 'users/set_user_info.html',
            reverse('users:logout'): 'users/logged_out.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.auth_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_set_user_info_not_allow_for_anonim(self):
        """Cтраница профиля не доступна анонимному пользователю."""
        response = self.anon_user.get(reverse('users:set_user_info'))
        self.assertRedirects(response, '/auth/login/?next=/auth/set_user_info/')

    def test_user_signup_page_has_correct_context(self):
        """На страницу регистрации нового пользователя
        передается правильная форма.
        """
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField
        }
        for value, expected_type in form_fields.items():
            with self.subTest(value=value):
                response = self.anon_user.get(reverse('users:signup'))
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected_type)

    def test_set_user_info_has_correct_form(self):
        """На страницу профиля пользователя передаются правильная форма."""
        form_fields = {
            'timezone': forms.fields.TypedChoiceField,
        }
        for value, expected_type in form_fields.items():
            with self.subTest(value=value):
                response = self.auth_user.get(reverse('users:set_user_info'))
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected_type)


class TestUserForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='test_user')
        cls.user = User.objects.create_user(username='auth_test_user')

    def setUp(self):
        self.anon_user = Client()
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

    def test_create_new_user(self):
        users_count = User.objects.count()
        form_data = {
            'first_name': 'new_test_user_first_name',
            'last_name': 'new_test_user_last_name',
            'username': 'new_test_user',
            'email': 'new_user@mail.user',
            'password1': '123456&873AAAaa',
            'password2': '123456&873AAAaa',
        }
        response = self.anon_user.post(
            reverse('users:signup'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('users:set_user_info'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='new_test_user_first_name',
                last_name='new_test_user_last_name',
                username='new_test_user',
                email='new_user@mail.user'
            ).exists()
        )

    def test_auth_user_can_change_user_info(self):
        """Авторизованный пользователь может поменять настройки в профиле."""
        form_data = {'timezone': 'Europe/Moscow'}
        response = self.auth_user.post(
            reverse('users:set_user_info'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:main'))
        self.assertTrue(
            UserProfile.objects.filter(
                user=self.user,
                timezone=form_data['timezone']
            ).exists()
        )
