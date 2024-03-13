from django_filters.rest_framework import DjangoFilterBackend

from projects.filters import ProjectFilter, ProjectRecommendedFilter


class ProjectFilterBackend(DjangoFilterBackend):
    def get_filterset_class(self, view, queryset=None):
        if view.action == 'list':
            return ProjectFilter
        if view.action == 'recommended':
            return ProjectRecommendedFilter
        return None
