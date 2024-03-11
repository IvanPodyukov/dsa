from django.urls import path, include
from rest_framework import routers

from api import views
from api.views import UserViewSet, ProfileViewSet, InterestViewSet, ProjectViewSet, CheckpointViewSet, \
    ParticipantViewSet, ApplicationViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'profiles', ProfileViewSet, basename='profiles')
router.register(r'interests', InterestViewSet, basename='interests')
router.register(r'projects', ProjectViewSet, basename='projects')
router.register(r'checkpoints', CheckpointViewSet, basename='checkpoints')
router.register(r'participants', ParticipantViewSet, basename='participants')
router.register(r'applications', ApplicationViewSet, basename='applications')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
]
