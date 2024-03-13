import django_filters
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.shortcuts import render
from django_filters import filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.mixins import RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ViewSet, GenericViewSet

from account.models import Profile, Interest
from api.filters import ProjectFilterBackend

from api.permissions import ProjectPermission, ApplicationPermission, ParticipantPermission, CheckpointPermission, \
    ProfilePermission
from api.serializers import UserSerializer, ProfileReadOnlySerializer, InterestSerializer, ProjectReadOnlySerializer, \
    CheckpointReadOnlySerializer, ParticipantSerializer, ProjectCreateSerializer, \
    ApplicationReadOnlySerializer, UserLoginSerializer, AuthUserSerializer, ProjectUpdateSerializer, \
    CheckpointUpdateSerializer, ProjectRecommendedSerializer, ProfileWriteOnlySerializer, UserRegisterSerializer
from api.utils import get_and_authenticate_user, create_user_account
from applications.models import Application
from checkpoints.models import Checkpoint
from projects.filters import ProjectFilter
from projects.models import Project, Participant

from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin


class UserViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'login':
            return UserLoginSerializer
        if self.action == 'register':
            return UserRegisterSerializer
        if self.action == 'profile':
            return ProfileReadOnlySerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['login', 'register']:
            return []
        return super().get_permissions()

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        user = self.get_object()
        profile = user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = create_user_account(**serializer.validated_data)
        data = AuthUserSerializer(user).data
        return Response(data=data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_and_authenticate_user(**serializer.validated_data)
        data = AuthUserSerializer(user).data
        return Response(data=data, status=status.HTTP_200_OK)


class ProfileViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Profile.objects.all()
    permission_classes = (ProfilePermission,)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return ProfileWriteOnlySerializer
        if self.action == 'user':
            return UserSerializer
        return ProfileReadOnlySerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        profile = request.user.profile
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def user(self, request, pk=None):
        profile = self.get_object()
        user = profile.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class InterestViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Interest.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        return InterestSerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        interests = Interest.objects.filter(interested_users=request.user.profile)
        serializer = self.get_serializer(interests, many=True)
        return Response(serializer.data)


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [ProjectFilterBackend]
    permission_classes = (ProjectPermission,)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        if self.action == 'recommended':
            return ProjectRecommendedSerializer
        if self.action == 'checkpoints':
            return CheckpointReadOnlySerializer
        if self.action == 'creator':
            return UserSerializer
        if self.action == 'participants':
            return ParticipantSerializer
        return ProjectReadOnlySerializer

    def perform_create(self, serializer):
        kwargs = {
            'creator': self.request.user
        }
        serializer.save(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        my_projects = Project.objects.filter(creator=request.user)
        serializer = self.get_serializer(my_projects, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def involved(self, request):
        involved_projects = Project.objects.filter(participants__participant=request.user).distinct()
        serializer = self.get_serializer(involved_projects, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        recommended_projects = Project.objects.exclude(status=Project.COMPLETED).filter(
            tags__interested_users=request.user.profile).annotate(
            number_of_vacancies=Count('participants', filter=Q(participants__participant=None), distinct=True),
            common_tags=Count('tags', distinct=True)
        ).distinct().filter(number_of_vacancies__gt=0)
        serializer = self.get_serializer(recommended_projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def checkpoints(self, request, pk=None):
        project = self.get_object()
        checkpoints = project.checkpoints.all()
        serializer = self.get_serializer(checkpoints, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def creator(self, request, pk=None):
        project = self.get_object()
        creator = project.creator
        serializer = self.get_serializer(creator)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        project = self.get_object()
        participants = project.participants.all()
        serializer = self.get_serializer(participants, many=True)
        return Response(serializer.data)


class CheckpointViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Checkpoint.objects.all()
    permission_classes = (CheckpointPermission,)

    def get_serializer_class(self):
        if self.action == 'project':
            return ProjectReadOnlySerializer
        if self.action in ['update', 'partial_update']:
            return CheckpointUpdateSerializer
        return CheckpointReadOnlySerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        projects = Project.objects.filter(participants__in=request.user.participations.all())
        checkpoints = Checkpoint.objects.filter(project__in=projects).order_by('deadline')
        serializer = self.get_serializer(checkpoints, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def project(self, request, pk=None):
        checkpoint = self.get_object()
        project = checkpoint.project
        serializer = self.get_serializer(project)
        return Response(serializer.data)


class ParticipantViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Participant.objects.all()
    permission_classes = (ParticipantPermission,)

    def get_serializer_class(self):
        if self.action in ['submit', 'applications']:
            return ApplicationReadOnlySerializer
        if self.action == 'project':
            return ProjectReadOnlySerializer
        if self.action == 'participant':
            return UserSerializer
        return ParticipantSerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        participants = Participant.objects.filter(participant=request.user)
        serializer = self.get_serializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        participant = self.get_object()
        if participant.participant is None:
            application = Application.objects.get_or_create(vacancy=participant, applicant=request.user)
            serializer = self.get_serializer(application)
            return Response(serializer.data)
        return Response({"message": "Набор заявок закрыт на данную вакансию"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        participant = self.get_object()
        if participant.participant == request.user or participant.project.creator == request.user:
            participant.participant = None
            participant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        participant = self.get_object()
        applications = participant.applications
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def project(self, request, pk=None):
        participant = self.get_object()
        project = participant.project
        serializer = self.get_serializer(project)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def participant(self, request, pk=None):
        participant = self.get_object()
        user = participant.participant
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class ApplicationViewSet(RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Application.objects.all()
    permission_classes = (ApplicationPermission,)

    def get_serializer_class(self):
        return ApplicationReadOnlySerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        applications = Application.objects.filter(applicant=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        application = self.get_object()
        participant = application.vacancy
        participant.participant = application.applicant
        participant.applications.all().delete()
        participant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
