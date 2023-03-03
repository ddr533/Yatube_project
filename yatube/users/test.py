from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class TestUserUrls(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user',
                                             password='test@12345')
        self.auth_user = Client()
        self.auth_user.force_login(self.user)

    def test_urls_status_code_for_auth_user(self):
        responce = self.auth_user.get(reverse('users:password_change'))
        self.assertEqual(responce.status_code, 200)


class TestUserPages(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='test_user',
                                             password='test@12345')
        self.auth_user = Client()
        self.auth_user.force_login(self.user)
        self.anon_user = Client()

    def test_pages_use_correct_templates(self):
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
            reverse('users:logout'): 'users/logged_out.html',
        }
        for reverse_name, template in templates_page_names.items():
            response = self.auth_user.get(reverse_name)
            self.assertTemplateUsed(response, template)

    def test_user_signup_page_has_correct_context(self):
        """
        На страницу регистрации нового пользователя
        передается правильная форма.
        """
        form_field = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
            'password1': forms.fields.CharField,
            'password2': forms.fields.CharField
        }
        for value, expected_type in form_field.items():
            with self.subTest(value=value):
                response = self.anon_user.get(reverse('users:signup'))
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected_type)


class TestUserForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User.objects.create_user(username='test_user')

    def setUp(self):
        self.anon_user = Client()

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
        self.assertRedirects(response, reverse('posts:main'))
        self.assertEqual(User.objects.count(), users_count + 1)
        self.assertTrue(
            User.objects.filter(
                first_name='new_test_user_first_name',
                last_name='new_test_user_last_name',
                username='new_test_user',
                email='new_user@mail.user'
            ).exists()
        )
