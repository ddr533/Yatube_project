from django.contrib.auth.admin import UserAdmin
from django.contrib import admin

from .models import UserProfile


class UserProfileAdmin(UserAdmin):
    list_display = ('user', 'timezone', )
    list_editable = ('timezone', )


admin.site.register(UserProfile, UserProfileAdmin)
