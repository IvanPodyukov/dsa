from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from applications.models import Application


class UserIsCreatorOfApplicationProjectMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        application = get_object_or_404(Application, pk=pk)
        project = application.vacancy.project
        if project.creator == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied