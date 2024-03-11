from django.urls import path

from projects import views

app_name = 'projects'

urlpatterns = [
    path('mine/', views.MyProjectListView.as_view(), name='my_projects_list'),
    path('create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('recommended/', views.RecommendedProjectListView.as_view(), name='recommended_projects_list'),
    path('<pk>/', views.ProjectDetailView.as_view(), name='project_info'),
    path('<pk>/participants/', views.ParticipantsListView.as_view(), name='participants_list'),
    path('<pk>/participants/<int:participant_pk>/', views.ParticipantApplicationsListView.as_view(),
         name='participant_applications_list'),
    path('<pk>/participants/<int:participant_pk>/leave/', views.ProjectLeaveView.as_view(),
         name='leave_project'),
    path('<pk>/participants/<int:participant_pk>/remove/', views.RemoveParticipantView.as_view(),
         name='remove_participant'),
    path('<pk>/participants/<int:participant_pk>/<int:application_pk>/accept/', views.ApplicationAcceptView.as_view(),
         name='application_accept'),
    path('<pk>/participants/<int:participant_pk>/<int:application_pk>/reject/', views.ApplicationRejectView.as_view(),
         name='application_reject'),
    path('<pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('<pk>/checkpoints/', views.CheckpointUpdateView.as_view(), name='checkpoints_update'),
    path('<int:project_pk>/<int:participant_pk>/submit/', views.ProjectSubmitView.as_view(), name='project_submit'),
    path('<int:project_pk>/<int:participant_pk>/withdraw/', views.ProjectWithdrawView.as_view(),
         name='project_withdraw'),
    path('', views.ProjectListView.as_view(), name='projects_list')
]
