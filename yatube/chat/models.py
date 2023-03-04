from django.db import models
from posts.models import Group, User



class Message(models.Model):
    text = models.TextField(max_length=300, blank=False)
    user = models.ForeignKey(to=User, related_name='chat_messages',
                             on_delete=models.CASCADE)
    group = models.ForeignKey(to=Group, related_name='group_chat',
                              on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('date_added',)
