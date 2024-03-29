from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from notifications.models import Notification


class NotificationIsForUserRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        pk = int(kwargs['pk'])
        notification = get_object_or_404(Notification, pk=pk)
        if notification.user == request.user:
            return super().dispatch(request, *args, **kwargs)
        raise PermissionDenied
