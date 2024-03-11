from django.contrib import messages
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST, require_GET
from django.views.generic import UpdateView

from account.forms import UserRegistrationForm, ProfileForm, LoginForm
from account.models import Profile


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = ProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(
                user_form.cleaned_data['password'])
            new_user.save()
            profile = profile_form.save(commit=False)
            profile.user = new_user
            profile.save()
            profile.interests.set(profile_form.cleaned_data['interests'])
            return render(request,
                          'account/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
        profile_form = ProfileForm()
    return render(request,
                  'account/register.html',
                  {'user_form': user_form,
                   'profile_form': profile_form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['identifier'],
                                password=form.cleaned_data['password'])
            if user is not None:
                login(request=request, user=user)
                return redirect(reverse('main'))
            else:
                messages.error(request, 'Неправильный логин/пароль')
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
        form.initial['interests'] = self.request.user.profile.interests.all()
        return form

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        self.request.user.profile.interests.set(form.cleaned_data['interests'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('account:profile')
