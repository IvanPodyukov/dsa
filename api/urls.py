from django.urls import path, include
from rest_framework import routers

from api.views import UserViewSet, InterestViewSet, ProjectViewSet, CheckpointViewSet, \
    ParticipantViewSet, ApplicationViewSet, InvolvedProjectList, MineProjectList

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'interests', InterestViewSet, basename='interests')
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'checkpoints', CheckpointViewSet, basename='checkpoints')
router.register(r'participants', ParticipantViewSet, basename='participants')
router.register(r'applications', ApplicationViewSet, basename='applications')

app_name = 'api'

urlpatterns = [
    path('projects/involved/', InvolvedProjectList.as_view(), name='involved'),
    path('projects/mine/', MineProjectList.as_view(), name='mine'),
    path('', include(router.urls)),
]

