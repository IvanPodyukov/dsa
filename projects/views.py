from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Avg
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView
from django_filters.views import FilterView

from participants.models import Participant
from projects.filters import ProjectFilter, ProjectRecommendedFilter
from projects.mixins import UserIsCreatorRequiredMixin
from projects.forms import ProjectCreateForm, CheckpointFormSet, ParticipantCreateFormSet, ProjectUpdateForm, RatingForm
from projects.models import Project, Rating
from projects.recommendation import recommend_projects


class ProjectListView(LoginRequiredMixin, FilterView):
    paginate_by = 5
    queryset = Project.objects.all().annotate(
        vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True),
        checkpoints_num=Count('checkpoints', distinct=True),
        participants_num=Count('participants', distinct=True),
    )
    context_object_name = 'projects'
    template_name = 'projects/list.html'
    filterset_class = ProjectFilter


class MyProjectListView(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    template_name = 'projects/my_list.html'

    def get_queryset(self):
        return self.request.user.created_projects.all()


class RatedProjectsView(LoginRequiredMixin, ListView):
    context_object_name = 'projects_and_forms'
    template_name = 'projects/rated_projects.html'
    paginate_by = 5

    def get_queryset(self):
        projects = Project.objects.filter(ratings__user=self.request.user)
        rating_forms = []
        for project in projects:
            form = RatingForm({'rating': project.ratings.get(user=self.request.user).rating})
            form.fields['rating'].label = ''
            rating_forms.append(form)
        return list(zip(projects, rating_forms))


class ProjectLeaderboardView(LoginRequiredMixin, ListView):
    context_object_name = 'projects'
    template_name = 'projects/leaderboard.html'
    paginate_by = 5

    def get_queryset(self):
        return Project.objects.filter(ratings__isnull=False).distinct().annotate(
            mean_rating=Avg('ratings__rating')).order_by(
            '-mean_rating')


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
                    cpt = checkpoint.save(commit=False)
                    cpt.project = self.object
                    cpt.save()
                for participant in participants:
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not self.object.ratings.filter(user=self.request.user).exists():
            rating = '-'
        else:
            rating = str(self.object.ratings.all().get(user=self.request.user).rating)
        context['rating_form'] = RatingForm({'rating': rating})
        return context


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
        projects = recommend_projects(self.request.user.pk).exclude(status=Project.COMPLETED).annotate(
            vacancies_num=Count('participants', filter=Q(participants__participant=None), distinct=True),
            checkpoints_num=Count('checkpoints', distinct=True),
            participants_num=Count('participants', distinct=True),
        ).distinct().filter(vacancies_num__gt=0)[:10]
        return projects


class CheckpointUpdateView(LoginRequiredMixin, UserIsCreatorRequiredMixin, UpdateView):
    model = Project
    fields = []
    template_name = 'projects/checkpoints.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['checkpoints'] = CheckpointFormSet(self.request.POST, instance=self.object)
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


class ProjectRateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        rating = request.POST.get('rating')
        if rating == '-':
            Rating.objects.filter(project=project, user=request.user).delete()
            messages.success(request, 'Рейтинг был удалён')
        else:
            rating = int(rating)
            project_rating, created = Rating.objects.get_or_create(defaults={'rating': rating}, project=project,
                                                                   user=request.user)
            if created:
                messages.success(request, 'Рейтинг был добавлен')
            else:
                messages.success(request, 'Рейтинг был изменён')
                project_rating.rating = rating
                project_rating.save()
        path = request.META.get('HTTP_REFERER')
        if path is None:
            return redirect(reverse('main'))
        return redirect(path)
