from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django_filters.views import FilterView

from participants.models import Participant
from projects.filters import ProjectFilter, ProjectRecommendedFilter
from projects.mixins import UserIsCreatorRequiredMixin
from projects.forms import ProjectCreateForm, CheckpointFormSet, ParticipantCreateFormSet, ProjectUpdateForm
from projects.models import Project


class ProjectListView(LoginRequiredMixin, FilterView):
    paginate_by = 5
    queryset = Project.objects.all().annotate(
        vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True),
        checkpoints_num=Count('checkpoints'),
        participants_num=Count('participants'),
    )
    context_object_name = 'projects'
    template_name = 'projects/list.html'
    filterset_class = ProjectFilter


class MyProjectListView(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    template_name = 'projects/my_list.html'

    def get_queryset(self):
        return self.request.user.created_projects.all()


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


class RecommendedProjectListView(LoginRequiredMixin, FilterView):
    context_object_name = 'projects'
    template_name = 'projects/recommended_projects.html'
    filterset_class = ProjectRecommendedFilter
    paginate_by = 5

    def get_queryset(self):
        projects = Project.objects.exclude(status=Project.COMPLETED).filter(
            tags__interested_users=self.request.user).annotate(
            vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True),
            common_tags=Count('tags', distinct=True),
            checkpoints_num=Count('checkpoints'),
            participants_num=Count('participants'),
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
