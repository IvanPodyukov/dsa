from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.views.generic import ListView

from checkpoints.models import Checkpoint
from projects.models import Project


class CheckpointListView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        projects = Project.objects.filter(participants__in=self.request.user.participations.all())
        checkpoints = Checkpoint.objects.filter(project__in=projects)
        return checkpoints.order_by('deadline')

    template_name = 'checkpoints/list.html'
    context_object_name = 'checkpoints'
