import django_filters
from django.forms import CheckboxSelectMultiple
from django.db import models
from django_filters import OrderingFilter

from account.models import Interest
from projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        conjoined=True
    )
    ordering = OrderingFilter(
        fields=(
            ('created', 'created'),
            ('application_deadline', 'application_deadline'),
            ('completion_deadline', 'completion_deadline'),
        )
    )

    class Meta:
        model = Project
        fields = ['status']
