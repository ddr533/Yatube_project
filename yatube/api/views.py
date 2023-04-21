from rest_framework import viewsets, filters

from api.serializers import GroupSerializer, GroupDetailSerializer
from api.permissions import AdminOnlyPermission
from posts.models import Group


class GroupViewSet(viewsets.ModelViewSet):
    """
    Информация о сообществах.

    Для обычного пользователя доступны только методы GET, как для списка
    сообществ так и для отдельного сообщества. Администратору доступны все
    методы. При запросе списка сообществ загружаются только названия и
    описание групп. При запросе детальной информации о сообществе
    загружаются все поля из модели.
    """

    queryset = Group.objects.all()
    permission_classes = (AdminOnlyPermission, )
    filter_backends = (filters.SearchFilter, )
    search_fields = ('title', 'description')


    def get_serializer_class(self):
            if self.action == 'list':
                return GroupSerializer
            elif self.action == 'retrieve':
                return GroupDetailSerializer
            return super().get_serializer_class()