from django.urls import path
from . import views

app_name = 'chat'

urlpatterns = [
    path('', views.get_chats_list, name='chats_list'),
    path('<slug:group_slug>/', views.get_group_chat, name='group_chat'),
]