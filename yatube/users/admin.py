from django.contrib import admin
from .models import UserProfile


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'timezone', )
    list_editable = ('timezone', )


admin.site.register(UserProfile, UserProfileAdmin)