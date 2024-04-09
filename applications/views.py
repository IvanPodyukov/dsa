from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from applications.mixins import UserIsCreatorOfApplicationProjectMixin
from applications.models import Application
from notifications.utils import create_notifications_application_accept, create_notification_application_reject


class ApplicationListView(LoginRequiredMixin, ListView):
    context_object_name = 'applications'
    template_name = 'applications/list.html'

    def get_queryset(self):
        return Application.objects.filter(applicant=self.request.user)


class ApplicationAcceptView(LoginRequiredMixin, UserIsCreatorOfApplicationProjectMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        participant = application.vacancy
        participant.participant = application.applicant
        create_notifications_application_accept(application)
        participant.applications.all().delete()
        participant.save()
        return redirect(reverse('projects:participants_list', args=(participant.project.pk,)))


class ApplicationRejectView(LoginRequiredMixin, UserIsCreatorOfApplicationProjectMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        participant = application.vacancy
        create_notification_application_reject(application)
        application.delete()
        return redirect(reverse('participants:participant_applications_list', args=(participant.pk,)))
