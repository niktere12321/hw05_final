from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='AA')
        cls.test_group = Group.objects.create(title='tests')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date=Post.pub_date,
            author=cls.user,
            group=cls.test_group
        )

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'текст поста',
            'group': 'группа',
        }
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).verbose_name, expected)

    def test_help_text(self):
        """help_text в полях совпадает с ожидаемым."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Напишите, о чем ваш пост',
            'group': 'Выберите группу из списка',
        }
        for value, expected in field_help_texts.items():
            with self.subTest(value=value):
                self.assertEqual(
                    post._meta.get_field(value).help_text, expected)

    def test_str_post(self):
        """правильно ли отображается
        значение поля __str__ в модели Post"""
        post = PostModelTest.post
        expected_object_name = post.text
        self.assertEquals(expected_object_name, str(post.text))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовое описание',
        )

    def test_str_group(self):
        """правильно ли отображается
        значение поля __str__ в модели Group"""
        group = GroupModelTest.group
        expected_object_name = group.title
        self.assertEquals(expected_object_name, str(group.title))
