from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Case, When, Value, ManyToManyField, Count, F
from django.forms import forms
from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django_filters.views import FilterView

from account.models import Interest
from projects.filters import ProjectFilter
from projects.mixins import UserIsCreatorRequiredMixin
from applications.models import Application
from projects.forms import ProjectCreateForm, CheckpointFormSet, ParticipantCreateFormSet, ProjectUpdateForm, \
    CheckpointInlineFormSet
from projects.models import Project, Participant


class ProjectListView(LoginRequiredMixin, FilterView):
    queryset = Project.objects.all()
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
        participant = get_object_or_404(Participant, pk=participant_pk, project=project_pk)
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
        participant = get_object_or_404(Participant, pk=participant_pk, project=project_pk)
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
        participant.applications.all().delete()
        return redirect(reverse('projects:participants_list', args=(pk,)))


class ApplicationRejectView(LoginRequiredMixin, UserIsCreatorRequiredMixin, View):
    def post(self, request, pk, participant_pk, application_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        application = get_object_or_404(Application, custom_id=application_pk, vacancy=participant)
        application.delete()
        return redirect(reverse('projects:participant_applications_list', args=(pk, participant_pk)))


class RemoveParticipantView(LoginRequiredMixin, UserIsCreatorRequiredMixin, View):
    def post(self, request, pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        participant.participant = None
        participant.save()
        return redirect(reverse('projects:participants_list', args=(pk,)))


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


class ProjectLeaveView(LoginRequiredMixin, View):
    def post(self, request, pk, participant_pk):
        participant = get_object_or_404(Participant, custom_id=participant_pk, project=pk)
        participant.participant = None
        participant.save()
        return redirect(reverse('projects:my_projects_list'))


class RecommendedProjectListView(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    template_name = 'projects/recommended_projects.html'

    def get_queryset(self):
        projects = Project.objects.filter(tags__interested_users=self.request.user.profile).annotate(
            common_tags=Count('tags')
        ).distinct()
        return projects.order_by('-common_tags')


class CheckpointUpdateView(LoginRequiredMixin, UpdateView):
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
