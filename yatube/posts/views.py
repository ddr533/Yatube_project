import time
from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import get_user_model
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render


from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User

User = get_user_model()

#Декоратор для тестирования скорости выполнения функций
def execute_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        res = func(*args, **kwargs)
        stop = time.time()
        print(stop-start)
        return res
    return wrapper


def get_page_obj_paginator(request, post_list):
    paginator = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {'page_obj': page_obj}


# @cache_page(20, key_prefix='index_page')
# @vary_on_cookie
# @execute_time
def index(request):
    posts_list = cache.get('posts_list')
    if not posts_list:
        posts_list = (Post.objects.select_related('author')
                 .select_related('group').all())
        cache.set('posts_list', posts_list, 20)
    context = get_page_obj_paginator(request, posts_list)
    context.update({'title': 'Последние записи'})
    return render(request, template_name='posts/index.html', context=context)


# @execute_time
def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    group_post_list = group.posts.select_related('author').all()
    context = get_page_obj_paginator(request, group_post_list)
    context.update({'group': group})
    return render(request, template_name='posts/group_list.html',
                  context=context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.select_related('group').all()
    context = get_page_obj_paginator(request, user_posts)
    context.update({'author': author})
    following = (request.user.is_authenticated
                 and Follow.objects.filter(user=request.user,
                                           author=author).exists())
    context.update({'following': following})
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = (get_object_or_404(Post.objects.select_related('author')
                              .annotate(count=Count('author__posts')),
                              id=post_id))
    comments = post.comments.select_related('author').all()
    comment_form = CommentForm()
    context = {'post': post, 'comments': comments,
               'comment_form': comment_form}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        author = request.user
        post = form.save(commit=False)
        post.author = author
        post.save()
        return redirect('posts:profile', author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author or not request.user.is_authenticated:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': True, 'post_id': post_id}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_delete(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    post.delete()
    return redirect('posts:profile', post.author.username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
# @cache_page(20, key_prefix='follow_page')
# @vary_on_cookie
def follow_index(request):
    posts = (Post.objects.select_related('author').select_related('group')
             .filter(author__following__user=request.user))
    context = get_page_obj_paginator(request, posts)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    if user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = get_object_or_404(Follow, user=request.user, author=author)
    follow.delete()
    return redirect('posts:main')


def get_search_result(request):
    text = request.GET.get('text')
    posts_search = (
        Post.objects.select_related('author').select_related('group')
        .filter(Q(text__contains=text)
                | Q(text__contains=text.lower())
                | Q(text__contains=text.capitalize())
                | Q(author__username__contains=text)
                | Q(author__first_name__contains=text)))
    context = get_page_obj_paginator(request, posts_search)
    context.update({'title': 'Результаты поиска'})
    return render(request, 'posts/index.html', context)


