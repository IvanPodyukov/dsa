from django.urls import path

from projects import views

app_name = 'projects'

urlpatterns = [
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('recommended/', views.RecommendedProjectListView.as_view(), name='recommended_projects_list'),
    path('mine/', views.MyProjectListView.as_view(), name='my_projects_list'),
    path('<pk>/', views.ProjectDetailView.as_view(), name='project_info'),
    path('<pk>/participants/', views.ParticipantsListView.as_view(), name='participants_list'),
    path('<pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<pk>/checkpoints/', views.CheckpointUpdateView.as_view(), name='checkpoints_update'),
    path('<pk>/delete/', views.ProjectDeleteView.as_view(), name='delete_project'),
    path('', views.ProjectListView.as_view(), name='projects_list')
]
