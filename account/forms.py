from django import forms
from django.contrib.auth.models import User
from django.forms import CheckboxSelectMultiple, models

from account.models import Profile, Interest


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль',
                               widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль',
                                widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']
        labels = {
            'username': 'Никнейм',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Электронная почта'
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Электронная почта уже используется.')
        return email

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Никнэйм уже используется.')
        return username

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают.')
        return cd['password2']


class ProfileForm(forms.ModelForm):
    interests = models.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        label='Научные интересы')

    class Meta:
        model = Profile
        fields = ['phone', 'cv']
        labels = {
            'phone': 'Номер телефона',
            'cv': 'Резюме',
        }


class LoginForm(forms.Form):
    identifier = forms.CharField(max_length=30, label='Идентификатор')
    password = forms.CharField(widget=forms.PasswordInput(), label='Пароль')
