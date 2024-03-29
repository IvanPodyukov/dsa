from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Value, ManyToManyField, Count, F, Q
from django.forms import forms
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django_filters.views import FilterView

from account.models import Interest
from notifications.models import Notification
from projects.filters import ProjectFilter, ProjectRecommendedFilter
from projects.mixins import UserIsCreatorRequiredMixin, UserIsCreatorOrParticipantRequiredMixin
from applications.models import Application
from projects.forms import ProjectCreateForm, CheckpointFormSet, ParticipantCreateFormSet, ProjectUpdateForm, \
    CheckpointInlineFormSet
from projects.models import Project, Participant


class ProjectListView(LoginRequiredMixin, FilterView):
    paginate_by = 5
    queryset = Project.objects.all().annotate(
        vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True))
    context_object_name = 'projects'
    template_name = 'projects/list.html'
    filterset_class = ProjectFilter


class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreateForm
    template_name = 'projects/create.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['form'] = ProjectCreateForm(self.request.POST)
            context['checkpoints'] = CheckpointFormSet(self.request.POST)
            context['participants'] = ParticipantCreateFormSet(self.request.POST)
        else:
            context['form'] = ProjectCreateForm()
            context['checkpoints'] = CheckpointFormSet()
            context['participants'] = ParticipantCreateFormSet()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        checkpoints = context['checkpoints']
        participants = context['participants']
        if form.is_valid():
            self.object = form.save(commit=False)
            checkpoints.instance = self.object
            participants.instance = self.object
            if checkpoints.is_valid() and participants.is_valid():
                # print(form.cleaned_data, 54, checkpoints.cleaned_data)
                self.object.creator = self.request.user
                self.object.save()
                self.object.tags.set(form.cleaned_data['tags'])
                for checkpoint in checkpoints:
                    if checkpoint.cleaned_data['DELETE']:
                        continue
                    cpt = checkpoint.save(commit=False)
                    cpt.project = self.object
                    cpt.save()
                for participant in participants:
                    if participant.cleaned_data['DELETE']:
                        continue
                    ppt = participant.save(commit=False)
                    ppt.project = self.object
                    ppt.save()
                return redirect(self.get_success_url())
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('projects:projects_list')


class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    context_object_name = 'project'
    template_name = 'projects/info.html'


class ProjectUpdateView(LoginRequiredMixin, UserIsCreatorRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectUpdateForm
    template_name = 'projects/update.html'

    def get_success_url(self):
        return reverse('projects:project_info', args=(self.object.pk,))


class ProjectSubmitView(LoginRequiredMixin, View):
    def post(self, request, project_pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=project_pk)
        _, created = Application.objects.get_or_create(vacancy=participant, applicant=request.user)
        if created:
            messages.success(request, 'Заявка была создана')
        else:
            messages.info(request, 'Заявка уже существует')
        path = request.META.get('HTTP_REFERER')
        if path is None:
            return redirect(reverse('main'))
        return redirect(path)


class ProjectWithdrawView(LoginRequiredMixin, View):
    def post(self, request, project_pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=project_pk)
        application = get_object_or_404(Application, vacancy=participant, applicant=request.user)
        application.delete()
        messages.success(request, 'Заявка отозвана')
        path = request.META.get('HTTP_REFERER')
        if path is None:
            return redirect(reverse('main'))
        return redirect(path)


class ParticipantsListView(LoginRequiredMixin, UserIsCreatorRequiredMixin, ListView):
    context_object_name = 'participants'
    template_name = 'projects/participants.html'

    def get_queryset(self):
        return Participant.objects.filter(project=self.kwargs['pk'])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        pk = self.kwargs['pk']
        context['project'] = Project.objects.get(pk=pk)
        return context


class ParticipantApplicationsListView(LoginRequiredMixin, UserIsCreatorRequiredMixin, ListView):
    context_object_name = 'applications'
    template_name = 'projects/applications.html'

    def get_queryset(self):
        vacancy = Participant.objects.get(project=self.kwargs['pk'], custom_id=self.kwargs['participant_pk'])
        return Application.objects.filter(vacancy=vacancy)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        participant_pk = self.kwargs['participant_pk']
        pk = self.kwargs['pk']
        context['participant'] = Participant.objects.get(custom_id=participant_pk, project=pk)
        return context


class ApplicationAcceptView(LoginRequiredMixin, UserIsCreatorRequiredMixin, View):
    def post(self, request, pk, participant_pk, application_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        application = get_object_or_404(Application, custom_id=application_pk, vacancy=participant)
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
        return redirect(reverse('projects:participants_list', args=(pk,)))


class ApplicationRejectView(LoginRequiredMixin, UserIsCreatorRequiredMixin, View):
    def post(self, request, pk, participant_pk, application_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        application = get_object_or_404(Application, custom_id=application_pk, vacancy=participant)
        text = f'Ваша заявка на роль {participant.title} в проекте {participant.project.title} отклонена'
        Notification.objects.create(user=application.applicant, text=text)
        application.delete()
        return redirect(reverse('projects:participant_applications_list', args=(pk, participant_pk)))


class ParticipantConfirmClearView(LoginRequiredMixin, UserIsCreatorOrParticipantRequiredMixin, View):
    def get(self, request, pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        if participant.participant == request.user:
            message = 'отказаться от роли'
        else:
            message = 'удалить участника из роли'
        return render(request, 'projects/confirm_clear_participant.html',
                      {'participant': participant, 'message': message})


class ParticipantClearView(LoginRequiredMixin, UserIsCreatorOrParticipantRequiredMixin, View):
    def post(self, request, pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        if participant.project.creator == request.user:
            text = f'Вы были удалены с роли {participant.title} в проекте {participant.project.title}'
            Notification.objects.create(user=participant.participant, text=text)
        participant.participant = None
        participant.save()
        return redirect(reverse('projects:project_info', args=(pk,)))


class MyProjectListView(LoginRequiredMixin, View):
    def get(self, request):
        my_projects = Project.objects.filter(creator=request.user)
        my_participations = Participant.objects.filter(participant=request.user)
        return render(request,
                      'projects/my_list.html',
                      {
                          'my_projects': my_projects,
                          'my_participations': my_participations
                      })


class RecommendedProjectListView(LoginRequiredMixin, FilterView):
    context_object_name = 'projects'
    template_name = 'projects/recommended_projects.html'
    filterset_class = ProjectRecommendedFilter
    paginate_by = 5

    def get_queryset(self):
        projects = Project.objects.exclude(status=Project.COMPLETED).filter(
            tags__interested_users=self.request.user).annotate(
            vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True),
            common_tags=Count('tags', distinct=True)
        ).distinct().filter(vacancies_num__gt=0)
        return projects


class CheckpointUpdateView(LoginRequiredMixin, UserIsCreatorRequiredMixin, UpdateView):
    model = Project
    fields = []
    template_name = 'projects/checkpoints.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['checkpoints'] = CheckpointFormSet(self.request.POST)
        else:
            context['checkpoints'] = CheckpointFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        checkpoints = context['checkpoints']
        if form.is_valid():
            checkpoints.instance = self.object
            if checkpoints.is_valid():
                self.object.checkpoints.all().delete()
                self.object.checkpoints_num = 0
                for checkpoint in checkpoints:
                    if checkpoint.cleaned_data['DELETE']:
                        continue
                    cpt = checkpoint.save(commit=False)
                    cpt.project = self.object
                    cpt.save()
                return redirect(self.get_success_url())
        return self.render_to_response(context)

    def get_success_url(self):
        return reverse('projects:project_info', args=(self.object.pk,))


class ProjectDeleteView(LoginRequiredMixin, UserIsCreatorRequiredMixin, DeleteView):
    model = Project
    template_name = 'projects/confirm_delete_project.html'

    def get_success_url(self):
        return reverse('projects:my_projects_list')
