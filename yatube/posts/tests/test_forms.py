import shutil
import tempfile
from io import BytesIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostsForms(TestCase):
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
        super().setUpClass()
        cls.test_group_1 = Group.objects.create(title='group_1', slug='slug_1')
        cls.test_group_2 = Group.objects.create(title='group_2', slug='slug_2')
        cls.test_user = User.objects.create_user(username='test_user')
        cls.post = Post.objects.create(text='text_post_1',
                                       author=cls.test_user,
                                       group=cls.test_group_1)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_user = Client()
        self.auth_user.force_login(self.test_user)

    def test_create_post(self):
        """Новая запись с картинкой сохраняется в БД."""
        post_count = Post.objects.count()
        image = self.get_image_for_test('post.bmp')
        form_data = {
            'text': 'text_post_2',
            'group': self.test_group_1.id,
            'image': image
        }
        response = self.auth_user.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:profile',
                                     kwargs={'username': self.test_user}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.test_group_1,
            author=self.test_user,
            image='posts/post.bmp'
        ).exists())

    def test_edit_post(self):
        """Отредактированная запись сохраняется в БД."""
        form_data = {
            'text': 'new_text_post_1',
            'group': self.test_group_2.id,
        }
        response = self.auth_user.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             reverse('posts:post_detail',
                                     kwargs={'post_id': self.post.id}))
        self.assertTrue(
            Post.objects.filter(
                id=self.post.id,
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
        self.assertEqual(Group.objects.get(
            slug=self.test_group_1.slug).posts.count(), 0)
        self.assertEqual(Group.objects.get(
            slug=self.test_group_2.slug).posts.count(), 1)

    def test_add_comment(self):
        """
        После успешного добавления комментарий
        появляется на странице записи.
        """
        page = reverse('posts:post_detail', kwargs={'post_id': self.post.id})
        comments_count = Comment.objects.filter(post=self.post.id).count()
        comment_form_data = {'text': 'new_test_comment', }
        response = self.auth_user.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=comment_form_data,
            follow=True
        )
        self.assertRedirects(response, page)
        self.assertEqual(Comment.objects.filter(post=self.post.id).count(),
                         comments_count + 1)
        response = self.auth_user.get(page)
        comment_on_page = response.context.get('comments')[0]
        self.assertEqual(comment_on_page.author, self.test_user)
        self.assertEqual(comment_on_page.post, self.post)
        self.assertEqual(comment_on_page.text, comment_form_data['text'])
