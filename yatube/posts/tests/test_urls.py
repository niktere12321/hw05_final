from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user_without_posts = User.objects.create_user(
            username='user_without_posts'
        )
        cls.group = Group.objects.create(
            title='Test group',
            slug='test-slug',
            description='description',
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group,
        )
        cls.URLs_list_for_guest = [
            '/',
            f'/group/{StaticURLTests.group.slug}/',
            f'/profile/{StaticURLTests.user.username}/',
            f'/posts/{StaticURLTests.post.id}/'
        ]
        cls.URLs_list_for_authorized = [
            '/create/',
            f'/posts/{cls.post.id}/edit/',
            '/follow/'
        ]

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(StaticURLTests.user)
        self.authorized_client_without_posts = Client()
        self.authorized_client_without_posts.force_login(
            StaticURLTests.user_without_posts
        )

    def test_URls_exists_at_desired_location_for_guest(self):
        """Страницы доступные любому пользователю."""
        for url in StaticURLTests.URLs_list_for_guest:
            with self.subTest(url=url):
                response = self.guest_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_URls_exists_at_desired_location_only_for_authorized(self):
        """Страницы доступные только авторизованному автору поста."""
        for url in StaticURLTests.URLs_list_for_authorized:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_new_and_post_edit_url_redirect_anonymous(self):
        """Страницы перенаправляющие анонимного пользователя."""
        login = reverse('login')

        for url in StaticURLTests.URLs_list_for_authorized:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)

                self.assertRedirects(response, f'{login}?next={url}')

    def test_post_edit_url_redirect_authorized_on_post_page(self):
        """Страница post_edit перенаправляет не автора поста."""
        post_id = StaticURLTests.post.id

        response = self.authorized_client_without_posts.get(
            f'/posts/{post_id}/edit/',
            follow=True
        )

        self.assertRedirects(response, f'/posts/{post_id}/')

    def test_urls_uses_correct_template(self):
        """URL-адреса использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{StaticURLTests.group.slug}/':
            'posts/group_list.html',
            f'/posts/{StaticURLTests.post.id}/': 'posts/post_detail.html',
            f'/profile/{StaticURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{StaticURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
            '/follow/': 'posts/follow.html'
        }

        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_return_not_found_code(self):
        """Сервер возвращает код 404, если страница не существует"""
        response = self.guest_client.get('/non/existen/page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
