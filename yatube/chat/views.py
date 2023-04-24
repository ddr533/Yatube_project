from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from posts.models import Group
from users.models import UserProfile


@login_required
def get_chats_list(request):
    chats_list = Group.objects.all()
    return render(request, 'chat/chats_list.html', {'chats_list': chats_list})


@login_required
def get_group_chat(request, group_slug):
    profile = UserProfile.objects.filter(user=request.user).first()
    time_zone = (timezone.get_current_timezone().zone
                 if not profile else profile.timezone)
    group = get_object_or_404(Group, slug=group_slug)
    messages = (group.group_chat.select_related('user').
                order_by('-date_added')[:20])
    messages = list(reversed(messages))
    context = {'messages': messages, 'group': group, 'time_zone': time_zone}
    return render(request, 'chat/group_chat.html', context)
