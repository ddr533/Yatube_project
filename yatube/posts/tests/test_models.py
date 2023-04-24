from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.following_user = User.objects.create_user(
            username='following_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text' * 10,
            group=cls.group
        )
        cls.follow = Follow.objects.create(
            user=cls.user,
            author=cls.following_user
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='comment' * 5
        )

    def test_models_have_correct_object_names(self):
        """У моделей корректно работает метод __str__."""
        expected_models_str_value = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
            self.follow: f'{self.user} подписан на {self.following_user}',
            self.comment: self.comment.text[:15]
        }
        for model_obj, expected_str_value in expected_models_str_value.items():
            with self.subTest(model_object=model_obj):
                self.assertEqual(expected_str_value, str(model_obj))

    def test_post_field_verbose_name(self):
        """В модели Post verbose_name полей совпадает с ожидаемым значением."""
        field_verbose_name = {
            'text': 'Текст поста',
            'group': 'Группа',
            'author': 'Автор',
        }
        for field, expected_verbose_name in field_verbose_name.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_verbose_name)

    def test_post_field_help_text(self):
        """В модели Post help_text совпадает с ожидаемым значением."""
        field_help_text = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        for field, expected_help_text in field_help_text.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).help_text,
                    expected_help_text)

    def test_get_absolute_url(self):
        """
        Тестирование метода get_absolute_url в моделях Group и Post.

        В модели Group метод возвращает ссылку на страницу группы.
        В модели Post метод возвращает страницу отдельной записи.
        """
        expected_urls_by_method = {
            self.post: reverse('posts:post_detail',
                               kwargs={'post_id': self.post.id}),
            self.group: reverse('posts:group_list',
                                kwargs={'slug': self.group.slug})
        }
        for model, expected_url in expected_urls_by_method.items():
            self.assertEqual(model.get_absolute_url(), expected_url)
