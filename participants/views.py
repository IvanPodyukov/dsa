from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from applications.models import Application
from notifications.models import Notification
from participants.mixins import UserIsCreatorOrParticipantRequiredMixin, UserIsCreatorParticipantProjectRequiredMixin
from participants.models import Participant


class MyParticipationsListView(LoginRequiredMixin, ListView):
    context_object_name = 'participations'
    template_name = 'participants/my_list.html'

    def get_queryset(self):
        return self.request.user.participations.all()


class ParticipantSubmitView(LoginRequiredMixin, View):
    def post(self, request, pk):
        participant = get_object_or_404(Participant, pk=pk)
        _, created = Application.objects.get_or_create(vacancy=participant, applicant=request.user)
        if created:
            messages.success(request, 'Заявка была создана')
        else:
            messages.info(request, 'Заявка уже существует')
        path = request.META.get('HTTP_REFERER')
        if path is None:
            return redirect(reverse('main'))
        return redirect(path)


class ParticipantWithdrawView(LoginRequiredMixin, View):
    def post(self, request, pk):
        participant = get_object_or_404(Participant, pk=pk)
        application = get_object_or_404(Application, vacancy=participant, applicant=request.user)
        application.delete()
        messages.success(request, 'Заявка отозвана')
        path = request.META.get('HTTP_REFERER')
        if path is None:
            return redirect(reverse('main'))
        return redirect(path)


class ParticipantApplicationsListView(LoginRequiredMixin, UserIsCreatorParticipantProjectRequiredMixin, ListView):
    context_object_name = 'applications'
    template_name = 'participants/applications.html'

    def get_queryset(self):
        vacancy = Participant.objects.get(pk=self.kwargs['pk'])
        return vacancy.applications.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['participant'] = Participant.objects.get(pk=pk)
        return context


class ParticipantConfirmClearView(LoginRequiredMixin, UserIsCreatorOrParticipantRequiredMixin, View):
    def get(self, request, pk):
        participant = get_object_or_404(Participant, pk=pk)
        if participant.participant == request.user:
            message = 'отказаться от роли'
        else:
            message = 'удалить участника из роли'
        return render(request, 'participants/confirm_clear_participant.html',
                      {'participant': participant, 'message': message})


class ParticipantClearView(LoginRequiredMixin, UserIsCreatorOrParticipantRequiredMixin, View):
    def post(self, request, pk):
        participant = get_object_or_404(Participant, pk=pk)
        if participant.project.creator == request.user:
            text = f'Вы были удалены с роли {participant.title} в проекте {participant.project.title}'
            Notification.objects.create(user=participant.participant, text=text)
        participant.participant = None
        participant.save()
        return redirect(reverse('projects:project_info', args=(participant.project.pk,)))
