import shutil
import tempfile
from io import BytesIO

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from ..models import Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostsPages(TestCase):
    @staticmethod
    def get_image_for_test(name: str) -> SimpleUploadedFile:
        with BytesIO() as output:
            Image.new('RGB', (1280, 1024), color=1).save(output, 'BMP')
            data = output.getvalue()
        image = SimpleUploadedFile(
            name=name,
            content=data,
            content_type='image'
        )
        return image

    @classmethod
    def setUpClass(cls):
        """Создаем 3 тестовых записи с различными авторами,
        группами и картинкой.
        """
        super().setUpClass()
        image = cls.get_image_for_test('post.bmp')
        # Пользователь, который будет подписываться
        cls.user = User.objects.create_user(username='test_user')
        # Пользователь, на которого будет подписываться cls.user
        cls.following_user = User.objects.create_user(username='following')
        # Пользователь без подписчиков и подписок
        cls.lonely_user = User.objects.create_user(username='lonely')
        cls.group_1 = Group.objects.create(title='test_group_1', slug='slug_1')
        cls.group_2 = Group.objects.create(title='test_group_2', slug='slug_2')
        cls.post_1 = Post.objects.create(author=cls.user,
                                         text='text_post_1')
        cls.post_2 = Post.objects.create(author=cls.following_user,
                                         group=cls.group_1,
                                         text='text_post_2')
        cls.post_3 = Post.objects.create(author=cls.user,
                                         group=cls.group_2,
                                         text='text_post_3',
                                         image=image)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_user = Client()
        self.auth_user.force_login(self.user)
        self.auth_lonely_user = Client()
        self.auth_lonely_user.force_login(self.lonely_user)
        self.not_auth_user = Client()
        cache.clear()

    def test_auth_user_can_follow_and_unfollow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        response = self.auth_user.get(reverse('posts:follow_index'))
        posts_before_following = (
            response.context.get('page_obj').paginator.count)
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following_user.username}))
        cache.clear()
        response = self.auth_user.get(reverse('posts:follow_index'))
        posts_after_following = (
            response.context.get('page_obj').paginator.count)
        self.assertEqual(posts_after_following, posts_before_following + 1)
        self.auth_user.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following_user.username}))
        cache.clear()
        posts_after_unfollowing = (
            response.context.get('page_obj').paginator.count)
        self.assertEqual(posts_after_following, posts_after_unfollowing)

    def test_new_following_post_on_folowers_page(self):
        """Новая запись отображается на странице подписчиков
        и не отображается на странице подписок других пользователей.
        """
        # Подписываемся на пользователя cls.following_user.
        self.auth_user.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following_user.username}))
        # Считаем число записей на странице
        # follow пользователя cls.following_user
        response = self.auth_user.get(reverse('posts:follow_index'))
        posts_before_new_post = (
            response.context.get('page_obj').paginator.count)
        cache.clear()
        # Создаем новую запись у пользователя cls.following_user.
        new_post = Post.objects.create(author=self.following_user,
                                       text='new_post')
        # Проверяем, что запись появилась на странице подписчика.
        response = self.auth_user.get(reverse('posts:follow_index'))
        posts_after_new_post = (
            response.context.get('page_obj').paginator.count)
        self.assertEqual(posts_after_new_post, posts_before_new_post + 1)
        self.assertEqual(response.context['page_obj'][0], new_post)
        cache.clear()
        # Проверяем, что у пользователя без подписок cls.lonely_user
        # по-прежнему нет записей на странице follow.
        response = self.auth_lonely_user.get(reverse('posts:follow_index'))
        self.assertFalse(response.context.get('page_obj').paginator.count)
        new_post.delete()

    def test_cache_working_on_main_page(self):
        """Работает кэш на главной страниц.
        Удаленная запись сохраняется в кэше 20 секунд
        и выводится на главную страницу.
        """
        Post.objects.create(author=self.user, text='test_cache')
        response = self.auth_user.get(reverse('posts:main'))
        content_before_the_del = response.content
        Post.objects.get(id=4, text='test_cache').delete()
        response = self.auth_user.get(reverse('posts:main'))
        content_after_the_del = response.content
        self.assertEqual(content_after_the_del, content_before_the_del)
        cache.clear()
        response = self.auth_user.get(reverse('posts:main'))
        content_after_clear_cach = response.content
        self.assertNotEqual(content_after_clear_cach, content_before_the_del)

    def test_pages_with_page_obj_has_image(self):
        """На главную страницу, страницу группы и в профайл автора
        в словарь context передается запись с картинкой (cls.post_3).
        """
        pages = (
            reverse('posts:main'),
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.auth_user.get(page)
                post_with_image = response.context['page_obj'][0]
                self.assertEqual(post_with_image.image, 'posts/post.bmp')

    def test_post_detail_page_has_image(self):
        """На страницу записи передается запись (cls.post_3)
         с картинкой в словарь context.
         """
        post_detail_page = reverse('posts:post_detail',
                                   kwargs={'post_id': self.post_3.id})
        response = self.auth_user.get(post_detail_page)
        self.assertEqual(response.context['post'].image, 'posts/post.bmp')

    def test_auth_user_can_add_comment(self):
        """Авторизованный пользователь может оставлять комментарии."""
        response_auth_user = self.auth_user.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': self.post_1.id}))
        form_field = (
            response_auth_user.context.get('comment_form').fields.get('text'))
        self.assertIsInstance(form_field, forms.CharField)

    def test_pages_uses_correct_template(self):
        """Во view-функциях используются соответствующие шаблоны.
         Переопределена страница 404.
         """
        templates_page_names = {
            '/not_exists_page/': 'core/404.html',
            reverse('posts:main'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}):
                'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}):
                'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.auth_user.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_main_page_has_correct_context(self):
        """На главной странице отображаются правильные данные
        из словаря context - список всех постов.
        """
        response = self.auth_user.get(reverse('posts:main'))
        self.assertEqual(response.context['page_obj'].paginator.count, 3)
        first_post = response.context['page_obj'][-1]
        self.assertEqual(first_post.text, self.post_1.text)
        self.assertIsNone(first_post.group)

    def test_group_list_has_correct_context(self):
        """На странице группы отображается правильные данные
        из словаря context - отфильтрованный по группе список постов.
        """
        response = self.auth_user.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}))
        self.assertEqual(response.context['page_obj'].paginator.count, 1)
        first_post = response.context['page_obj'][-1]
        self.assertEqual(first_post.text, self.post_2.text)
        self.assertEqual(first_post.group, self.group_1)

    def test_user_profile_has_correct_context(self):
        """На странице пользователя отображается корректные данные
        из словаря context - отфильтрованный по автору список постов.
        """
        response = self.auth_user.get(
            reverse('posts:profile', kwargs={'username': self.user.username}))

        self.assertEqual(response.context['page_obj'].paginator.count, 2)
        first_post = response.context['page_obj'][-1]
        self.assertEqual(first_post.author, self.user)
        self.assertEqual(first_post.text, self.post_1.text)

    def test_post_detail_has_correct_context(self):
        """На страницу записи передается один пост, отфильтрованный по id."""
        response = self.auth_user.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post_1.id}))
        post = response.context.get('post')
        self.assertIsInstance(post, Post)
        self.assertEqual(post.text, self.post_1.text)
        self.assertIsNone(post.group)

    def test_post_edit_page_has_correct_context(self):
        """На страницу редактирования записи передается форма."""
        response = self.auth_user.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post_1.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post_id'], self.post_1.id)
        self.assertEqual(response.context['form'].instance, self.post_1)

    def test_post_create_page_has_correct_context(self):
        """На страницу создания записи передается форма."""
        response = self.auth_user.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_with_group_show_on_pages(self):
        """Записи с объявленной группой отображаются на главной странице,
        странице автора и странице группы.
        """
        pages_with_post_with_group_1 = (
            reverse('posts:main'),
            reverse('posts:group_list', kwargs={'slug': self.group_2.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for page in pages_with_post_with_group_1:
            with self.subTest(page=page):
                response = self.auth_user.get(page)
                post = response.context['page_obj'][0]
                self.assertEqual(post.group, self.group_2)

    def test_group_list_has_only_own_posts(self):
        """На странице группы отображатся только принадлежащие
        этой группе записи.
        """
        response_group_1 = self.auth_user.get(
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}))
        self.assertTrue(all(post.group == self.group_1
                            for post in response_group_1.context['page_obj']))
        self.assertFalse(any(post.group == self.group_2
                             for post in response_group_1.context['page_obj']))

    def test_author_can_delete_own_post(self):
        """Автор может удалить свою запись."""
        new_post = Post.objects.create(author=self.user, text='new_post')
        response = self.auth_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_till_del = response.context.get('page_obj').paginator.count
        response = self.auth_user.get(reverse(
            'posts:post_del', kwargs={'post_id': new_post.id}))
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': new_post.author.username}))
        response = self.auth_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_after_del = response.context.get('page_obj').paginator.count
        self.assertEqual(count_posts_after_del, count_posts_till_del - 1)

    def test_non_author_cant_delete_post(self):
        """Авторизованный пользователь, не являющийся автором,
         не может удалить запись.
         """
        new_post = Post.objects.create(author=self.user, text='new_post')
        response = self.auth_lonely_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_till_del = response.context.get('page_obj').paginator.count
        response = self.auth_lonely_user.get(reverse(
            'posts:post_del', kwargs={'post_id': new_post.id}))
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': new_post.id}))
        response = self.auth_lonely_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_after_del = response.context.get('page_obj').paginator.count
        self.assertEqual(count_posts_after_del, count_posts_till_del)
        new_post.delete()

    def test_non_auth_user_cant_delete_post(self):
        """Не авторизованный пользовтаель не может удалить запись."""
        new_post = Post.objects.create(author=self.user, text='new_post')
        response = self.not_auth_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_till_del = response.context.get('page_obj').paginator.count
        response = self.not_auth_user.get(reverse(
            'posts:post_del', kwargs={'post_id': new_post.id}))
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{new_post.id}/delete/')
        response = self.not_auth_user.get(reverse(
            'posts:profile', kwargs={'username': new_post.author}))
        count_posts_after_del = response.context.get('page_obj').paginator.count
        self.assertEqual(count_posts_after_del, count_posts_till_del)
        new_post.delete()


@override_settings(CACHES={
    'default':{'BACKEND': 'django.core.cache.backends.dummy.DummyCache',}})
class TestPaginatorViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.group_1 = Group.objects.create(title='test_group_1', slug='slug_1')
        post_list = []
        for i in range(11):
            post_list.append(
                Post(text=f'text_post_{i}',
                     author=cls.user,
                     group=cls.group_1))
        Post.objects.bulk_create(post_list)

    def setUp(self):
        self.anon_user = Client()

    def test_paginator_for_pages(self):
        """Paginator работает и выводит по 10 записей на страницу."""
        pages_with_paginator = (
            reverse('posts:main'),
            reverse('posts:group_list', kwargs={'slug': self.group_1.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        for page in pages_with_paginator:
            with self.subTest(page=page):
                response_page_1 = self.anon_user.get(page)
                response_page_2 = self.anon_user.get(page + '?page=2')
                self.assertEqual(len(response_page_1.context['page_obj']), 10)
                self.assertEqual(len(response_page_2.context['page_obj']), 1)
