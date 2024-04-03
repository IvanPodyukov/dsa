from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from participants.models import Participant


class UserIsCreatorParticipantProjectRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        participant = get_object_or_404(Participant, pk=pk)
        if participant.project.creator == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied


class UserIsCreatorOrParticipantRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        participant = get_object_or_404(Participant, pk=pk)
        if participant.project.creator == request.user or participant.participant == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied