from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from projects.models import Project, Participant


class UserIsCreatorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        project = get_object_or_404(Project, pk=pk)
        if project.creator == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class UserIsParticipantRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        participant_pk = int(kwargs['participant_pk'])
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        if participant.participant == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class UserIsCreatorOrParticipantRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        participant_pk = int(kwargs['participant_pk'])
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        if participant.project.creator == request.user or participant.participant == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
