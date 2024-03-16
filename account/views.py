import requests
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, get_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView, DetailView

from account.forms import LoginForm, ProfileForm
from account.models import User


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email, password = form.cleaned_data['email'], form.cleaned_data['password']
            user = authenticate(email=email, password=password)
            if user is None:
                messages.error(request, 'Неправильный логин/пароль')
            else:
                login(request=request, user=user)
                return redirect(reverse('main'))

    else:
        form = LoginForm()
        return render(request,
                      'account/login.html',
                      {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    return redirect(reverse('main'))


@login_required
@require_GET
def profile(request):
    return render(request, 'account/profile.html')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "account/profile_update.html"
    form_class = ProfileForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.initial['interests'] = self.request.user.interests.all()
        return form

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        self.request.user.interests.set(form.cleaned_data['interests'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('account:profile')


class UserDetailView(LoginRequiredMixin, DetailView):
    model = User
    template_name = 'account/user_detail.html'
