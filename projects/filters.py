import django_filters
from django.forms import CheckboxSelectMultiple
from django_filters import OrderingFilter

from account.models import Interest
from projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Название содержит')
    description = django_filters.CharFilter(lookup_expr='icontains', label='Описание содержит')
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        conjoined=True,
        label='Теги'
    )
    ordering = OrderingFilter(
        fields=(
            ('created', 'Дата создания'),
            ('application_deadline', 'Дедлайн подачи заявки'),
            ('completion_deadline', 'Дедлайн завершения'),
            ('checkpoints_num', 'Количество контрольных точек'),
            ('participants_num', 'Количество участников'),
            ('vacancies_num', 'Количество вакансий'),
        ),
        label='Отсортировать по'
    )

    class Meta:
        model = Project
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['status'].label = 'Статус'
        choices = self.filters['ordering'].extra['choices']
        self.filters['ordering'].extra['choices'] = [(x, y.replace('descending', 'убывающий')) for x, y in choices]


class ProjectRecommendedFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains', label='Название содержит')
    description = django_filters.CharFilter(lookup_expr='icontains', label='Описание содержит')
    tags = django_filters.ModelMultipleChoiceFilter(
        queryset=Interest.objects.all(),
        widget=CheckboxSelectMultiple,
        conjoined=True,
        label='Теги'
    )
    ordering = OrderingFilter(
        fields=(
            ('created', 'Дата создания'),
            ('application_deadline', 'Дедлайн подачи заявки'),
            ('completion_deadline', 'Дедлайн завершения'),
            ('checkpoints_num', 'Количество контрольных точек'),
            ('participants_num', 'Количество участников'),
            ('vacancies_num', 'Количество вакансий'),
            ('expected_rating', 'Прогнозируемый рейтинг')
        ),
        label='Отсортировать по'
    )

    class Meta:
        model = Project
        fields = ['status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.filters['status'].label = 'Статус'
        choices = self.filters['ordering'].extra['choices']
        self.filters['ordering'].extra['choices'] = [(x, y.replace('descending', 'убывающий')) for x, y in choices]

    def filter_queryset(self, queryset):
        result = super().filter_queryset(queryset)
        return result[:10]
