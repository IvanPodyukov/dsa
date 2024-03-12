import django_filters
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db.models import Count
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
from api.permissions import ProjectPermission, ApplicationPermission, ParticipantPermission, CheckpointPermission
from api.serializers import UserSerializer, ProfileReadOnlySerializer, InterestSerializer, ProjectReadOnlySerializer, \
    CheckpointReadOnlySerializer, ParticipantSerializer, ProjectCreateSerializer, \
    ApplicationReadOnlySerializer, UserLoginSerializer, AuthUserSerializer, ProjectUpdateSerializer, \
    CheckpointUpdateSerializer
from api.utils import get_and_authenticate_user
from applications.models import Application
from checkpoints.models import Checkpoint
from projects.filters import ProjectFilter
from projects.models import Project, Participant

from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin


class UserViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.action == 'login':
            return []
        return super().get_permissions()

    @action(detail=False, methods=['get'])
    def current(self, request):
        user = request.user
        serializer = UserSerializer(user, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_and_authenticate_user(**serializer.validated_data)
        print(user)
        data = AuthUserSerializer(user).data
        return Response(data=data, status=status.HTTP_200_OK)

    '''
    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        data = {'success': 'Sucessfully logged out'}
        return Response(data=data, status=status.HTTP_200_OK)
    '''


class ProfileViewSet(ListModelMixin, RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileReadOnlySerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['get'])
    def current(self, request):
        profile = request.user.profile
        serializer = ProfileReadOnlySerializer(profile, context={'request': request})
        return Response(serializer.data)


class InterestViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Interest.objects.all()
    serializer_class = InterestSerializer
    permission_classes = (IsAuthenticated,)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        interests = Interest.objects.filter(interested_users=request.user.profile)
        serializer = InterestSerializer(interests, many=True, context={'request': request})
        return Response(serializer.data)


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    filterset_class = ProjectFilter
    permission_classes = (ProjectPermission,)

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        return ProjectReadOnlySerializer

    def perform_create(self, serializer):
        kwargs = {
            'creator': self.request.user
        }
        serializer.save(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        my_projects = Project.objects.filter(creator=request.user)
        serializer = ProjectReadOnlySerializer(my_projects, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def involved(self, request):
        involved_projects = Project.objects.filter(participants__participant=request.user).distinct()
        serializer = ProjectReadOnlySerializer(involved_projects, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        recommended_projects = Project.objects.filter(tags__interested_users=self.request.user.profile).annotate(
            common_tags=Count('tags')
        ).distinct()
        serializer = ProjectReadOnlySerializer(recommended_projects, many=True, context={'request': request})
        return Response(serializer.data)


class CheckpointViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Checkpoint.objects.all()
    serializer_class = CheckpointReadOnlySerializer
    permission_classes = (CheckpointPermission,)

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return CheckpointUpdateSerializer
        return CheckpointReadOnlySerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        projects = Project.objects.filter(participants__in=request.user.participations.all())
        checkpoints = Checkpoint.objects.filter(project__in=projects).order_by('deadline')
        serializer = CheckpointReadOnlySerializer(checkpoints, many=True, context={'request': request})
        return Response(serializer.data)


class ParticipantViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Participant.objects.all()
    serializer_class = ParticipantSerializer
    permission_classes = (ParticipantPermission,)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        participants = Participant.objects.filter(participant=request.user)
        serializer = ParticipantSerializer(participants, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        try:
            participant = self.get_object()
        except Participant.DoesNotExist:
            return Response({"error": "Participant not found."}, status=status.HTTP_404_NOT_FOUND)

        if participant.participant is None:
            application = Application.objects.get_or_create(vacancy=participant, applicant=request.user)
            serializer = ApplicationReadOnlySerializer(application, context={'request': request})
            return Response(serializer.data)
        return Response({"message": "Набор заявок закрыт на данную вакансию"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        try:
            participant = self.get_object()
        except Participant.DoesNotExist:
            return Response({"error": "Participant not found."}, status=status.HTTP_404_NOT_FOUND)
        if participant.participant == request.user or participant.project.creator == request.user:
            participant.participant = None
            participant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ApplicationViewSet(RetrieveModelMixin, DestroyModelMixin, CreateModelMixin, GenericViewSet):
    queryset = Application.objects.all()
    serializer_class = ApplicationReadOnlySerializer
    permission_classes = (ApplicationPermission,)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        applications = Application.objects.filter(applicant=request.user)
        serializer = ApplicationReadOnlySerializer(applications, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        try:
            application = self.get_object()
        except Application.DoesNotExist:
            return Response({"error": "Application not found."}, status=status.HTTP_404_NOT_FOUND)
        participant = application.vacancy
        participant.participant = application.applicant
        participant.save()
        application.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
