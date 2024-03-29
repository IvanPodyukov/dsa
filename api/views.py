from django.db.models import Count, Q

from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.generics import ListAPIView
from rest_framework.mixins import DestroyModelMixin, UpdateModelMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema

from rest_framework.viewsets import ModelViewSet, GenericViewSet

from account.models import Interest, User
from api.filters import ProjectFilterBackend

from api.pagination import ProjectPagination, CheckpointPagination

from api.permissions import ProjectPermission, ApplicationPermission, ParticipantPermission, CheckpointPermission, \
    UserPermission, NotificationPermission
from api.serializers import UserInfoSerializer, InterestSerializer, ProjectReadOnlySerializer, \
    CheckpointReadOnlySerializer, ParticipantSerializer, ProjectCreateSerializer, \
    ApplicationReadOnlySerializer, UserLoginSerializer, AuthUserSerializer, ProjectUpdateSerializer, \
    CheckpointUpdateSerializer, ProjectRecommendedSerializer, UserUpdateSerializer, NotificationSerializer
from api.utils import get_and_authenticate_user
from applications.models import Application
from checkpoints.models import Checkpoint
from notifications.models import Notification
from projects.filters import ProjectFilter
from projects.models import Project, Participant

from rest_framework.mixins import ListModelMixin, CreateModelMixin, RetrieveModelMixin


class UserViewSet(RetrieveModelMixin, UpdateModelMixin, GenericViewSet):
    queryset = User.objects.all()
    permission_classes = (UserPermission,)

    def get_serializer_class(self):
        if self.action == 'login':
            return UserLoginSerializer
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserInfoSerializer

    def get_permissions(self):
        if self.action == 'login':
            return []
        return super().get_permissions()

    @swagger_auto_schema(responses={
        201: AuthUserSerializer()
    })
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_and_authenticate_user(**serializer.validated_data)
        data = AuthUserSerializer(user).data
        return Response(data=data, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={
        200: UserInfoSerializer()
    })
    @action(detail=False, methods=['get'])
    def profile(self, request):
        user = request.user
        serializer = self.get_serializer(user)
        return Response(serializer.data)


class InterestViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Interest.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        return InterestSerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        interests = Interest.objects.filter(interested_users=request.user)
        serializer = self.get_serializer(interests, many=True)
        return Response(serializer.data)


class InvolvedProjectList(ListAPIView):
    serializer_class = ProjectReadOnlySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Project.objects.filter(participants__participant=self.request.user).distinct()


class MineProjectList(ListAPIView):
    serializer_class = ProjectReadOnlySerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Project.objects.filter(creator=self.request.user)


class ProjectViewSet(ModelViewSet):
    queryset = Project.objects.all()
    filter_backends = [ProjectFilterBackend]
    permission_classes = (ProjectPermission,)
    pagination_class = ProjectPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        if self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        if self.action == 'recommended':
            return ProjectRecommendedSerializer
        if self.action == 'checkpoints':
            return CheckpointReadOnlySerializer
        if self.action == 'participants':
            return ParticipantSerializer
        return ProjectReadOnlySerializer

    def perform_create(self, serializer):
        kwargs = {
            'creator': self.request.user
        }
        serializer.save(**kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def recommended(self, request):
        recommended_projects = self.filter_queryset(self.get_queryset()).exclude(status=Project.COMPLETED).filter(
            tags__interested_users=request.user).annotate(
            number_of_vacancies=Count('participants', filter=Q(participants__participant=None), distinct=True),
            common_tags=Count('tags', distinct=True)
        ).distinct().filter(number_of_vacancies__gt=0)
        page = self.paginate_queryset(recommended_projects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recommended_projects, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={
        200: CheckpointReadOnlySerializer(many=True)
    })
    @action(detail=True, methods=['get'])
    def checkpoints(self, request, pk=None):
        project = self.get_object()
        checkpoints = project.checkpoints.all()
        serializer = self.get_serializer(checkpoints, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={
        200: ParticipantSerializer(many=True)
    })
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        project = self.get_object()
        participants = project.participants.all()
        serializer = self.get_serializer(participants, many=True)
        return Response(serializer.data)


class CheckpointViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Checkpoint.objects.all()
    permission_classes = (CheckpointPermission,)
    pagination_class = CheckpointPagination

    def get_serializer_class(self):
        if self.action in ['update', 'partial_update']:
            return CheckpointUpdateSerializer
        return CheckpointReadOnlySerializer

    @action(detail=False, methods=['get'])
    def mine(self, request):
        projects = Project.objects.filter(participants__in=request.user.participations.all())
        checkpoints = Checkpoint.objects.filter(project__in=projects).order_by('deadline')
        page = self.paginate_queryset(checkpoints)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(checkpoints, many=True)
        return Response(serializer.data)


class ParticipantViewSet(UpdateModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Participant.objects.all()
    permission_classes = (ParticipantPermission,)

    def get_serializer_class(self):
        if self.action == 'applications':
            return ApplicationReadOnlySerializer
        return ParticipantSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action in ['clear', 'submit']:
            return None
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        participants = Participant.objects.filter(participant=request.user)
        serializer = self.get_serializer(participants, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={201: ApplicationReadOnlySerializer()})
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        participant = self.get_object()
        if participant.participant is None:
            application, _ = Application.objects.get_or_create(vacancy=participant, applicant=request.user)
            serializer = ApplicationReadOnlySerializer(application, context={'request': request})
            return Response(serializer.data)
        return Response({"message": "Набор заявок закрыт на данную вакансию"}, status=status.HTTP_200_OK)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=True, methods=['post'])
    def clear(self, request, pk=None):
        participant = self.get_object()
        if participant.participant == request.user or participant.project.creator == request.user:
            participant.participant = None
            participant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={
        200: ApplicationReadOnlySerializer(many=True)
    })
    @action(detail=True, methods=['get'])
    def applications(self, request, pk=None):
        participant = self.get_object()
        applications = participant.applications
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)


class ApplicationViewSet(RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Application.objects.all()
    permission_classes = (ApplicationPermission,)

    def get_serializer_class(self):
        return ApplicationReadOnlySerializer

    def get_serializer(self, *args, **kwargs):
        if self.action == 'accept':
            return None
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        applications = Application.objects.filter(applicant=request.user)
        serializer = self.get_serializer(applications, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        application = self.get_object()
        participant = application.vacancy
        participant.participant = application.applicant
        participant.applications.all().delete()
        participant.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class NotificationViewSet(RetrieveModelMixin, DestroyModelMixin, GenericViewSet):
    queryset = Notification.objects.all()
    permission_classes = (NotificationPermission,)

    def get_serializer_class(self):
        return NotificationSerializer

    def get_serializer(self, *args, **kwargs):
        if self.action in ['read', 'unread', 'read_all', 'unread_all']:
            return None
        return super().get_serializer(*args, **kwargs)

    @action(detail=False, methods=['get'])
    def mine(self, request):
        notifications = request.user.notifications.all()
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=False, methods=['post'])
    def read_all(self, request):
        notifications = request.user.notifications.all()
        notifications.update(unread=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=False, methods=['post'])
    def unread_all(self, request):
        notifications = request.user.notifications.all()
        notifications.update(unread=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=True, methods=['post'])
    def read(self, request, pk):
        notification = self.get_object()
        notification.unread = False
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={204: ""})
    @action(detail=True, methods=['post'])
    def unread(self, request, pk):
        notification = self.get_object()
        notification.unread = True
        notification.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
