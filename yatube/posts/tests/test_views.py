import os
import shutil

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Comment, Follow, Group, Post

User = get_user_model()


class CommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='Тестовый автор')
        cls.user = User.objects.create(username='Тестовый пользователь')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый текст',
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Тестовый комментарий'
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(CommentTest.user)
        self.form_data = {'post': 'Тестовый комментарий'}

    def unauthorized_user_cant_comment(self):
        """Не авторизированный пользователь не может комментировать посты."""
        response = self.guest_client.post(reverse(
            'add_comment', args=[CommentTest.author.username,
                                 CommentTest.post.id]))
        self.assertRedirects(response, reverse(
            'post', args=[CommentTest.author.username,
                          CommentTest.post.id]))

    def authorized_user_can_comment(self):
        """Только авторизированный пользователь может комментировать посты."""
        self.authorized_client.post(reverse(
            'add_comment',
            args=[CommentTest.author.username, CommentTest.post.id]),
            data=self.form_data, follow=True)
        self.assertTrue(
            Comment.objects.filter(post='Тестовый комментарий').exists())
        self.assertTrue(
            Comment.objects.get(post='Тестовый комментарий').text,
            CommentTest.comment.text)
        self.assertTrue(
            Comment.objects.get(post='Тестовый комментарий').author,
            CommentTest.comment.author)


@override_settings(MEDIA_ROOT=os.path.join(settings.BASE_DIR,
                                           'temp_views_test'))
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test_user',
        )
        cls.group_with_post = Group.objects.create(
            title='Test Group with post',
            slug='test-slug-of-group-with-post',
            description='Test group(1) description',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00'
            b'\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00'
            b'\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Test text',
            author=cls.user,
            group=cls.group_with_post,
            image=uploaded
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        # Создаём неавторизованный клиент
        self.guest_client = Client()
        # Создаём авторизованный клиент
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTests.user)

    def context_page_assertions(self, page_object, tets_post):
        self.assertEqual(page_object.text, PostPagesTests.post.text)
        self.assertEqual(page_object.pub_date, PostPagesTests.post.pub_date)
        self.assertEqual(page_object.author, PostPagesTests.post.author)
        self.assertEqual(page_object.id, PostPagesTests.post.id)
        self.assertEqual(page_object.image, PostPagesTests.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.pk}
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.pk}
            ): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group_with_post.slug}
            ): 'posts/group_list.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        # Проверяем, что при обращении к name
        # вызывается соответствующий HTML-шаблон
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)

                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        first_object = 0
        test_post = PostPagesTests.post

        response = self.guest_client.get(reverse('posts:index'))
        page_object = response.context['page_obj'][first_object]

        self.assertIn('page_obj', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)

    # Проверяем, что словарь context страницы /task
    # в первом элементе списка object_list содержит ожидаемые значения
    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        group = PostPagesTests.group_with_post
        first_object = 0
        test_post = PostPagesTests.post

        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': PostPagesTests.group_with_post.slug})
        )
        page_object = response.context['page_obj'][first_object]
        response_group = response.context['group']

        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        self.assertContains(response, '<img')
        self.context_page_assertions(page_object, test_post)
        self.assertEqual(response_group.title, group.title)
        self.assertEqual(response_group.slug, group.slug)
        self.assertEqual(response_group.description, group.description)

    # Проверяем, что словарь context страницы group/test-slug
    # содержит ожидаемые значения
    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.pk})
        )
        self.assertEqual(response.context['post'].author.username, 'test_user')
        self.assertEqual(response.context['post'].text, 'Test text')
        self.assertEqual(response.context['post'].group.title,
                         'Test Group with post')

    def test_post_create_page_show_correct_context(self):
        """Шаблон create post сформирован с правильным контекстом."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        response = self.authorized_client.get(reverse('posts:post_create'))

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]

                self.assertIsInstance(form_field, expected)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            kwargs={'username': PostPagesTests.user.username})
        )
        author_object = response.context['author']

        self.assertIn('author', response.context)
        self.assertEqual(author_object.get_username(),
                         PostPagesTests.user.username)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.pk})
        )
        post_id_object = response.context['post']

        self.assertIn('post', response.context)
        self.assertEqual(post_id_object, PostPagesTests.post)

    def test_paginator_show_correct_context(self):
        """Проверка правильности контекста paginator на всех страницах"""
        view_setting_paginator = 10
        batch_size = 15
        posts = [
            Post(text=f'Infinity text {i}',
                 group=PostPagesTests.group_with_post,
                 author=PostPagesTests.user)
            for i in range(batch_size)
        ]
        Post.objects.bulk_create(posts, batch_size)
        count_all_posts = Post.objects.count()
        pages = {
            '?page=1': view_setting_paginator,
            '?page=2': count_all_posts - view_setting_paginator
        }
        templates_page_names = {
            'posts:index.html': reverse('posts:index'),
            'posts:group_list.html': reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group_with_post.slug}
            ),
            'posts:profile.html': reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}
            )
        }
        pages_with_paginator = ['posts:index.html',
                                'posts:group_list.html',
                                'posts:profile.html']

        for page_urls in pages_with_paginator:
            for number_page, count_post_on_page in pages.items():
                with self.subTest():
                    response = self.guest_client.get(
                        templates_page_names[page_urls] + number_page
                    )
                    count_objects = len(response.context['page_obj'])

                    self.assertEqual(count_objects, count_post_on_page)

    def test_index_page_cache(self):
        """Проверка кеширования index page"""
        first_response = self.guest_client.get(reverse('posts:index'))
        new_post = Post.objects.create(
            text='Another test publication',
            author=PostPagesTests.user,
        )

        last_response = self.guest_client.get(reverse('posts:index'))

        self.assertEqual(first_response.content, last_response.content,
                         'Проверка кеширования')

        cache.clear()
        response = self.guest_client.get(reverse('posts:index'))

        self.assertIn(new_post, response.context['page_obj'],
                      'Проверка отчистки кеша')


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.follower = User.objects.create(username='Тестовый подписчик')
        cls.author_1 = User.objects.create(username='Тестовый автор 1')
        cls.follow = Follow.objects.create(author=cls.author_1,
                                           user=cls.follower)
        cls.post = Post.objects.create(
            author=cls.author_1,
            text='Тестовый текст',
        )
        cls.author_2 = User.objects.create(username='Тестовый автор 2')

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(FollowTest.follower)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(FollowTest.author_2)

    def test_user_can_follow_author(self):
        """Авторизованный пользователь может
        подписываться на других пользователей."""
        self.authorized_client_1.get(reverse(
                'posts:profile_follow', args=[FollowTest.author_2.username]))
        self.assertEqual(Follow.objects.get(user=FollowTest.follower,
                                            author=FollowTest.author_2).author,
                         FollowTest.author_2)

    def test_user_cant_follow_author(self):
        """Неавторизованный не может
        подписываться на других пользователей."""
        self.guest_client.get(reverse(
                'posts:profile_follow', args=[FollowTest.author_2.username]))
        self.assertFalse(
            Follow.objects.filter(user=FollowTest.follower,
                                  author=FollowTest.author_2).exists()
        )

    def test_user_can_unfollow_author(self):
        """Авторизованный пользователь может
        удалять других пользователей из подписок."""
        self.authorized_client_1.get(
                reverse('posts:profile_unfollow',
                        args=[FollowTest.author_2.username]))
        self.assertFalse(Follow.objects.filter(
            user=FollowTest.follower, author=FollowTest.author_2).exists())

    def test_profile_follow(self):
        """Проверка системы подписок profile_follow"""
        unsubscribed_user = FollowTest.follower
        subscribed_user = FollowTest.author_1

        self.assertFalse(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists(),
            'Объект Follow уже существует, тест test_profile_follow '
            '- неисправен'
        )

        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_subscribed.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': unsubscribed_user})
        )

        self.assertTrue(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists()
        )

    def test_profile_unfollow(self):
        """Проверка системы подписок profile_unfollow"""
        unsubscribed_user = FollowTest.follower
        subscribed_user = FollowTest.author_1
        Follow.objects.create(author=unsubscribed_user,
                              user=subscribed_user)

        authorized_subscribed = Client()
        authorized_subscribed.force_login(subscribed_user)
        authorized_subscribed.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': unsubscribed_user})
        )

        self.assertFalse(
            Follow.objects.filter(
                author=unsubscribed_user,
                user=subscribed_user
            ).exists()
        )
