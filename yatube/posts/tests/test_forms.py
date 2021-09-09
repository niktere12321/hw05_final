import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Group, Post

User = get_user_model()

MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='man')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.new_group = Group.objects.create(
            title='New test group',
            slug='new-test-group',
            description='Description test group',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
            group=cls.group,
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(PostFormTests.author)

    def test_create_posts(self):
        """Валидная форма создает запись в Post."""
        # Подсчитаем количество записей в Post
        posts_count = Post.objects.count()
        form_data = {
            'text': 'new text',
            'group': PostFormTests.group.pk,
            'image': PostFormTests.uploaded
        }
        # Отправляем POST-запрос
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response,
                             reverse(
                                 'posts:profile',
                                 kwargs={'username': self.author.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                author=PostFormTests.author,
                text=form_data['text'],
                group=PostFormTests.group.pk).exists())
        last_object = Post.objects.filter().order_by('-id').first()
        self.assertEqual(last_object.text, form_data['text'])
        self.assertEqual(last_object.author, form_data['author'])
        self.assertEqual(last_object.group.id, form_data['group'])
        self.assertEqual(last_object.image.name, 'posts/small.gif')

    def test_create_posts(self):
        """Валидная форма изменяет запись в Post"""
        post_id = PostFormTests.post.pk
        form_data = {
            'text': 'New test text',
            'group': PostFormTests.new_group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True,
        )
        PostFormTests.post.refresh_from_db()
        self.assertRedirects(response, reverse('posts:post_detail',
                                               kwargs={'post_id': post_id}))
        self.assertEqual(PostFormTests.post.text, form_data['text'])
        self.assertEqual(PostFormTests.post.group.pk,
                         form_data['group'])

    def test_create_comment_guest(self):
        """Неавторизованный пользователь не может создать comment в Post."""
        post_id = PostFormTests.post.pk
        form_data = {
            'text': 'Test news comment',
        }

        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_id}),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Comment.objects.filter(
                text='Test news comment',
                author=PostFormTests.author,
                post=PostFormTests.post.id
            ).exists()
        )
