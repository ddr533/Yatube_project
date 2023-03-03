from django import forms
from posts.models import Comment, Post


class PostForm(forms.ModelForm):
    class Meta():
        # labels и help_text определены в моделях
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
