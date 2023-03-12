from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import CreationForm, UserProfileForm
from .models import UserProfile


class SignUp(CreateView):
    form_class = CreationForm
    success_url = reverse_lazy('users:set_user_info')
    template_name = 'users/signup.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)


@login_required
def set_user_info(request):
    profile = UserProfile.objects.get_or_create(user=request.user)[0]
    form = UserProfileForm(request.POST or None, instance=profile)
    if form.is_valid():
        profile.save()
        return redirect('posts:main')
    return render(request, 'users/set_user_info.html', {'form': form})

