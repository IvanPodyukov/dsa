import datetime

from django import forms
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import models, inlineformset_factory, DateInput, BaseInlineFormSet, CheckboxSelectMultiple

from account.models import Interest
from checkpoints.models import Checkpoint
from participants.models import Participant
from projects.models import Project, Rating


class CheckpointCreateForm(models.ModelForm):
    class Meta:
        model = Checkpoint
        fields = ['title', 'description', 'deadline']
        widgets = {
            'deadline': DateInput(attrs={
                'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)',
                'class': 'form-control'
            })}
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'deadline': 'Дедлайн контрольной точки'
        }


class ParticipantCreateForm(models.ModelForm):
    class Meta:
        model = Participant
        fields = ['title', 'description']
        labels = {
            'title': 'Название',
            'description': 'Описание'
        }


class CheckpointInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        last_deadline = None
        last_form = None
        for form in self.forms:
            d = form.cleaned_data
            if not d:
                form.add_error(None, forms.ValidationError('Должна быть заполнена информация в контрольной точке'))
                continue
            if last_deadline and last_deadline >= d['deadline']:
                form.add_error(None, forms.ValidationError(
                    'У контрольной точки не может дедлайн быть раньше дедлайна предыдущей'))
                continue
            if 'deadline' not in d:
                form.add_error(None, forms.ValidationError(
                    'Заполните дедлайн у контрольной точки'))
                continue
            if not last_deadline and self.instance.application_deadline and d[
                'deadline'] <= self.instance.application_deadline:
                form.add_error(None,
                               forms.ValidationError(
                                   'Дедлайн контрольной точки не может быть раньше дедлайна подачи заявки'))
                continue
            last_deadline = d['deadline']
            last_form = form
        if self.instance.completion_deadline and last_deadline and last_deadline >= self.instance.completion_deadline:
            last_form.add_error(None,
                                forms.ValidationError(
                                    'Дедлайн контрольной точки не может быть позже дедлайна выполнения проекта'))


class ParticipantInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        count = 0
        for form in self.forms:
            d = form.cleaned_data
            if not d:
                form.add_error(None, forms.ValidationError('Должна быть заполнена информация об участнике'))
                continue
            count += 1
        if count == 0:
            raise forms.ValidationError('Не может быть 0 участников')


CheckpointFormSet = inlineformset_factory(
    Project,
    Checkpoint,
    form=CheckpointCreateForm,
    extra=0,
    can_delete=False,
    formset=CheckpointInlineFormSet
)

ParticipantCreateFormSet = inlineformset_factory(
    Project,
    Participant,
    form=ParticipantCreateForm,
    extra=0,
    can_delete=False,
    formset=ParticipantInlineFormSet
)


class ProjectCreateForm(models.ModelForm):
    tags = models.ModelMultipleChoiceField(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        label='Теги')

    class Meta:
        model = Project
        fields = ['title', 'description', 'application_deadline', 'completion_deadline']
        widgets = {
            'application_deadline': DateInput(attrs={
                'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)',
                'class': 'form-control'
            }),
            'completion_deadline': DateInput(attrs={
                'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'application_deadline': 'Дедлайн подачи заявки',
            'completion_deadline': 'Срок завершения проекта',
        }

    def clean(self):
        super().clean()
        completion_deadline = self.cleaned_data['completion_deadline']
        application_deadline = self.cleaned_data['application_deadline']
        if datetime.date.today() >= application_deadline:
            raise forms.ValidationError('Дедлайн подачи заявки не может быть раньше сегодняшнего дня')
        if completion_deadline <= application_deadline:
            raise forms.ValidationError('Дедлайн выполнения проекта не может быть раньше дедлайна подачи заявок')


class ProjectUpdateForm(models.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'status', 'application_deadline', 'completion_deadline']
        widgets = {
            'application_deadline': DateInput(attrs={
                'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)',
                'class': 'form-control'
            }),
            'completion_deadline': DateInput(attrs={
                'type': 'date', 'placeholder': 'yyyy-mm-dd (DOB)',
                'class': 'form-control'
            }),
        }
        labels = {
            'title': 'Название',
            'description': 'Описание',
            'status': 'Статус',
            'application_deadline': 'Дедлайн подачи заявки',
            'completion_deadline': 'Срок завершения проекта',
        }

    def clean(self):
        super().clean()
        completion_deadline = self.cleaned_data['completion_deadline']
        application_deadline = self.cleaned_data['application_deadline']
        if self.instance.application_deadline != application_deadline and datetime.date.today() >= application_deadline:
            raise forms.ValidationError('Дедлайн подачи заявки не может быть раньше сегодняшнего дня')
        if completion_deadline <= application_deadline:
            raise forms.ValidationError('Дедлайн выполнения проекта не может быть раньше дедлайна подачи заявок')
        checkpoints = self.instance.checkpoints.all()
        if checkpoints:
            if application_deadline >= checkpoints[0].deadline:
                raise forms.ValidationError('Дедлайн контрольной точки не может быть раньше дедлайна подачи заявок')
            if completion_deadline <= checkpoints[len(checkpoints) - 1].deadline:
                raise forms.ValidationError('Дедлайн контрольной точки не может быть позже дедлайна выполнения проекта')


class RatingForm(forms.Form):
    rating = forms.CharField(
        label='Рейтинг',
        widget=forms.Select(choices=[('-', '-')] + [(i, i) for i in range(0, 6)])
    )