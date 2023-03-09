import pytz
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from .models import Message
from posts.models import Group
from users.models import UserProfile
from django.utils import timezone



@login_required
def get_chats_list(request):
    chats_list = Group.objects.all()
    return render(request, 'chat/chats_list.html', {'chats_list': chats_list})


@login_required
def get_group_chat(request, group_slug):
    profile = UserProfile.objects.filter(user=request.user).first()
    time_zone = (timezone.get_current_timezone()
                 if not profile else profile.timezone)
    last_msg_id = Message.objects.last().id
    messages = (Message.objects.select_related('user').select_related('group')
                .filter(group__slug=group_slug, id__in=range(last_msg_id+20)))
    context = {'messages': messages, 'group': messages[0].group,
               'time_zone':time_zone}
    return render(request, 'chat/group_chat.html', context)

