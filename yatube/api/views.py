from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from api.serializers import (GroupSerializer, GroupDetailSerializer,
                             PostSerializer)

from api.permissions import AdminOnlyPermission, IsAuthorOrReadOnly
from posts.models import Group, Post
from rest_framework.pagination import LimitOffsetPagination


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