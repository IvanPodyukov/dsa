from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from applications.mixins import UserIsCreatorOfApplicationProjectMixin
from applications.models import Application
from notifications.models import Notification
from projects.mixins import UserIsCreatorRequiredMixin


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
        participant.save()
        text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} одобрена'
        Notification.objects.create(user=application.applicant, text=text)
        application.delete()
        remaining_applications = participant.applications.all()
        text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} отклонена'
        for application in remaining_applications:
            Notification.objects.create(user=application.applicant, text=text)
            application.delete()
        return redirect(reverse('projects:participants_list', args=(participant.project.pk,)))


class ApplicationRejectView(LoginRequiredMixin, UserIsCreatorOfApplicationProjectMixin, View):
    def post(self, request, pk):
        application = get_object_or_404(Application, pk=pk)
        participant = application.vacancy
        text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} отклонена'
        Notification.objects.create(user=application.applicant, text=text)
        application.delete()
        return redirect(reverse('participants:participant_applications_list', args=(participant.pk,)))
