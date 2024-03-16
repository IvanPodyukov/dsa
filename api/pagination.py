from rest_framework.pagination import PageNumberPagination


class ProjectPagination(PageNumberPagination):
    page_size = 5

    def paginate_queryset(self, queryset, request, view=None):
        if view.action not in ['list', 'recommended']:
            return None
        return super().paginate_queryset(queryset, request, view)


class CheckpointPagination(PageNumberPagination):
    page_size = 5

    def paginate_queryset(self, queryset, request, view=None):
        if view.action != 'mine':
            return None
        return super().paginate_queryset(queryset, request, view)
