from django.urls import path, include
from rest_framework import routers

app_name = 'api'

urlpatterns = [
    path('v1/auth/', include('djoser.urls')),
    path('v1/auth/', include('djoser.urls.jwt')),
]
