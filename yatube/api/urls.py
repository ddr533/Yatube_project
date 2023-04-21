from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls import url
from rest_framework.routers import DefaultRouter

from api.views import GroupViewSet

app_name = 'api'

router_v1 = DefaultRouter()
router_v1.register('groups', GroupViewSet, basename='group')


urlpatterns = [
    path('v1/auth/', include('djoser.urls')),
    path('v1/auth/', include('djoser.urls.jwt')),
    path('v1/', include(router_v1.urls)),
]


schema_view = get_schema_view(
   openapi.Info(
      title="Yatube API",
      default_version='v1',
      description="Документация для приложения проекта Yatube",
      # terms_of_service="URL страницы с пользовательским соглашением",
      # contact=openapi.Contact(email="admin@kittygram.ru"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
   url(r'^v1/swagger(?P<format>\.json|\.yaml)$',
       schema_view.without_ui(cache_timeout=0), name='schema-json'),
   url(r'^v1/swagger/$', schema_view.with_ui('swagger', cache_timeout=0),
       name='schema-swagger-ui'),
]
