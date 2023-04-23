from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, serializers, mixins
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import (GroupSerializer, GroupDetailSerializer,
                             PostSerializer, CommentSerializer,
                             FollowSerializer)

from api.permissions import (AdminOnlyPermission, IsAuthorOrReadOnly,
                             IsAuthenticatedAuthor)
from posts.models import Group, Post, Comment, Follow, User
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.viewsets import GenericViewSet


class PostViewSet(viewsets.ModelViewSet):
    """
    Информация о записях.

    Для всех типов пользователей доступен метод GET. Публиковать запись может
    только аутентифицированный пользователь. Изменять запись может только автор.
    Картинки передаются в строках как ссылки "http://.....", либо в формате
    base64 ""data:image/png;base64....."
    """

    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = (IsAuthorOrReadOnly,)
    filter_backends = (filters.SearchFilter, DjangoFilterBackend)
    search_fields = ('author__username', 'text')
    filterset_fields = ('author__username', 'group')
    pagination_class = LimitOffsetPagination

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)



class GroupViewSet(viewsets.ModelViewSet):
    """
    Информация о сообществах.

    Для пользователей доступен только метод GET. Как для списка
    сообществ так и для отдельного сообщества. Администратору доступны все
    методы. При запросе списка сообществ загружаются только названия и
    описания сообществ. При запросе детальной информации о сообществе
    загружаются все поля из модели.
    """

    queryset = Group.objects.all()
    permission_classes = (AdminOnlyPermission, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('title', 'description')
    pagination_class = None


    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GroupDetailSerializer
        return GroupSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """
    Комментарии к записям.

    Комментировать может только авторизованный пользователь.
    Изменять комментарии может только их автор.
    """

    queryset = Comment.objects.none()
    serializer_class = CommentSerializer
    permission_classes = (IsAuthorOrReadOnly, )
    filter_backends = (filters.SearchFilter, DjangoFilterBackend,
                       filters.OrderingFilter)
    search_fields = ('author__username', 'text', '^created')
    filterset_fields = ('author__username', )
    ordering_fields = '__all__'
    pagination_class = None

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)

    def get_queryset(self):
        post_id = self.kwargs.get('post_id')
        post = get_object_or_404(Post, id=post_id)
        return post.comments.all()


class FollowViewSet(GenericViewSet,
                    mixins.ListModelMixin,
                    mixins.CreateModelMixin,
                    mixins.DestroyModelMixin):
    """
    Информация о подписках.

    Получить список подписок, создавать и удалять свои подписки может только
    авторизованный пользователь.
    """

    queryset = Follow.objects.none()
    serializer_class = FollowSerializer
    permission_classes = (IsAuthenticatedAuthor, )
    pagination_class = None
    filter_backends = (filters.SearchFilter,)
    search_fields = ('author__username',)

    def get_queryset(self):
        user = self.request.user
        return user.follower.all()

    def perform_create(self, serializer):
        try:
            following = User.objects.get(
                username=serializer.validated_data['author'])
            serializer.save(user=self.request.user, author=following)

        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(
                f'Автора с таким именем нет в базе, {e}')

        except IntegrityError as e:
            raise serializers.ValidationError(
                f'Нельзя подписываться на самого себя и создавать'
                f' одинаковые подписки, {e}')
