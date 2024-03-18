from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import ListView

from applications.models import Application


class ApplicationListView(LoginRequiredMixin, ListView):
    context_object_name = 'applications'
    template_name = 'applications/list.html'

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)
