import pytz
from django.contrib.auth import get_user_model
from django.db import models

TIMEZONES = tuple(zip(pytz.all_timezones, pytz.all_timezones))

User = get_user_model()


class UserProfile(models.Model):
    user = models.OneToOneField(
        to=User,
        verbose_name='Пользователь',
        related_name='profile',
        on_delete=models.CASCADE
    )
    timezone = models.CharField(
        max_length=32,
        choices=TIMEZONES,
        default='UTC',
        blank=False
    )
