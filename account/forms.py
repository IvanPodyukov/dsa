from django import forms
from django.forms import CheckboxSelectMultiple, models

from account.models import Interest, User


class ProfileForm(forms.ModelForm):
    interests = models.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        label='Научные интересы',
        required=False)

    class Meta:
        model = User
        fields = ['phone', 'cv']
        labels = {
            'phone': 'Номер телефона',
            'cv': 'Резюме',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['phone'].required = False
        self.fields['cv'].required = False


class LoginForm(forms.Form):
    email = forms.EmailField(label='Электронная почта')
    password = forms.CharField(widget=forms.PasswordInput(), label='Пароль')
