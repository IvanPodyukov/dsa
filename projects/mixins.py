from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from participants.models import Participant
from projects.models import Project


class UserIsCreatorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        project = get_object_or_404(Project, pk=pk)
        if project.creator == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied



