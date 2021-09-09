from django.contrib.auth import get_user_model
from django.forms import ModelForm, Textarea

from .models import Comment, Post

User = get_user_model()


class PostForm(ModelForm):

    class Meta:
        model = Post
        fields = ['group', 'text', 'image']
        widgets = {
            'text': Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Введите текст'
            }),
        }
        labels = {
            'group': ('Группа'),
            'text': ('Текст'),
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widget = {'text': Textarea(attrs={'cols': 80, 'rows': 20})}
        labels = {
            'text': 'Текст',
        }
        help_texts = {
            'text': 'Текст нового комментария',
        }
