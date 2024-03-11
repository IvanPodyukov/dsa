import datetime

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.relations import HyperlinkedIdentityField, HyperlinkedRelatedField

from account.models import Profile, Interest
from checkpoints.models import Checkpoint
from projects.models import Project, Participant


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'title']


class ProfileReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    # interests = InterestSerializer(many=True)
    interests = HyperlinkedRelatedField(view_name='api:interests-detail', read_only=True, many=True)

    class Meta:
        model = Profile
        fields = ['id', 'phone', 'cv', 'interests']


class ProfileWriteOnlySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone', 'cv', 'interests']


class UserSerializer(serializers.HyperlinkedModelSerializer):
    profile = HyperlinkedRelatedField(view_name='api:profiles-detail', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email', 'profile', 'password']
        extra_kwargs = {'password': {'write_only': True}}


class UserLoginSerializer(serializers.Serializer):
    email = serializers.CharField(max_length=300, required=True)
    password = serializers.CharField(required=True, write_only=True)


class AuthUserSerializer(serializers.ModelSerializer):
    auth_token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'auth_token']
        read_only_fields = ['id']

    def get_auth_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key


class CheckpointReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    project = HyperlinkedRelatedField(view_name='api:projects-detail', read_only=True)

    class Meta:
        model = Checkpoint
        fields = ['id', 'custom_id', 'title', 'description', 'deadline', 'project']
        read_only_fields = ['custom_id']


class CheckpointCreateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['title', 'description', 'deadline']


class CheckpointUpdateSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['title', 'description']


class ParticipantSerializer(serializers.HyperlinkedModelSerializer):
    participant = HyperlinkedRelatedField(view_name='api:users-detail', read_only=True)
    project = HyperlinkedRelatedField(view_name='api:projects-detail', read_only=True)
    applications = HyperlinkedRelatedField(view_name='api:applications-detail', read_only=True, many=True)

    class Meta:
        model = Participant
        fields = ['id', 'title', 'description', 'participant', 'project', 'applications']


class ProjectReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    creator = HyperlinkedRelatedField(view_name='api:users-detail', read_only=True)
    tags = HyperlinkedRelatedField(view_name='api:interests-detail', read_only=True, many=True)
    checkpoints = HyperlinkedRelatedField(view_name='api:checkpoints-detail', read_only=True, many=True)
    participants = HyperlinkedRelatedField(view_name='api:participants-detail', read_only=True, many=True)

    class Meta:
        model = Project
        fields = ['id', 'title', 'creator', 'created', 'description', 'application_deadline', 'completion_deadline',
                  'status',
                  'tags', 'checkpoints', 'participants']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data


class ProjectCreateSerializer(serializers.ModelSerializer):
    checkpoints = CheckpointCreateSerializer(many=True)
    participants = ParticipantSerializer(many=True)

    class Meta:
        model = Project
        fields = ['title', 'description', 'application_deadline', 'completion_deadline', 'status', 'checkpoints',
                  'participants', 'tags']

    def validate_participants(self, value):
        print(self.context['view'].action)
        if len(value) == 0:
            raise serializers.ValidationError('Участников должно быть больше 0')
        return value

    def validate_checkpoints(self, value):
        last_deadline = None
        for checkpoint in value:
            if last_deadline and last_deadline >= checkpoint['deadline']:
                raise serializers.ValidationError(
                    'У контрольной точки не может дедлайн быть раньше дедлайна предыдущей')
            last_deadline = checkpoint['deadline']
        return value

    def validate(self, data):
        application_deadline = data['application_deadline']
        if datetime.date.today() >= application_deadline:
            raise serializers.ValidationError('Дедлайн подачи заявки не может быть раньше сегодняшнего дня')
        checkpoints = data['checkpoints']
        if checkpoints and application_deadline >= checkpoints[0]['deadline']:
            raise serializers.ValidationError(
                'Дедлайн контрольной точки не может быть раньше дедлайна подачи заявки')
        completion_deadline = data['completion_deadline']
        if completion_deadline <= application_deadline:
            raise serializers.ValidationError(
                'Дедлайн выполнения проекта не может быть раньше дедлайна подачи заявок')
        if checkpoints and completion_deadline <= checkpoints[-1]['deadline']:
            raise serializers.ValidationError(
                'Дедлайн контрольной точки не может быть позже дедлайна выполнения проекта')
        return data

    def create(self, validated_data):
        checkpoints_data = validated_data.pop('checkpoints')
        participants_data = validated_data.pop('participants')
        tags_ids = validated_data.pop('tags')
        project = Project.objects.create(**validated_data)
        project.tags.set(tags_ids)
        for participant_data in participants_data:
            Participant.objects.create(project=project, **participant_data)
        for checkpoint_data in checkpoints_data:
            Checkpoint.objects.create(project=project, **checkpoint_data)
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    checkpoints = CheckpointCreateSerializer(many=True)

    class Meta:
        model = Project
        fields = ['title', 'description', 'application_deadline', 'completion_deadline', 'status', 'checkpoints',
                  'tags']

    def validate_checkpoints(self, value):
        last_deadline = None
        for checkpoint in value:
            if last_deadline and last_deadline >= checkpoint['deadline']:
                raise serializers.ValidationError(
                    'У контрольной точки не может дедлайн быть раньше дедлайна предыдущей')
            last_deadline = checkpoint['deadline']
        return value

    def validate(self, data):
        application_deadline = data.get('application_deadline', self.instance.application_deadline)
        if datetime.date.today() >= application_deadline:
            raise serializers.ValidationError('Дедлайн подачи заявки не может быть раньше сегодняшнего дня')
        checkpoints = data.get('checkpoints', [])
        if checkpoints and application_deadline >= checkpoints[0]['deadline']:
            raise serializers.ValidationError(
                'Дедлайн контрольной точки не может быть раньше дедлайна подачи заявки')
        completion_deadline = data.get('completion_deadline', self.instance.completion_deadline)
        if completion_deadline <= application_deadline:
            raise serializers.ValidationError(
                'Дедлайн выполнения проекта не может быть раньше дедлайна подачи заявок')
        if checkpoints and completion_deadline <= checkpoints[-1]['deadline']:
            raise serializers.ValidationError(
                'Дедлайн контрольной точки не может быть позже дедлайна выполнения проекта')
        return data

    def update(self, instance, validated_data):
        if 'checkpoints' in validated_data:
            instance.checkpoints.all().delete()
            checkpoints_data = validated_data.pop('checkpoints')
            for checkpoint_data in checkpoints_data:
                Checkpoint.objects.create(project=instance, **checkpoint_data)
        if 'tags' in validated_data:
            tags_ids = validated_data.pop('tags')
            instance.tags.set(tags_ids)
        super().update(instance, validated_data)
        return instance


class ApplicationReadOnlySerializer(serializers.HyperlinkedModelSerializer):
    vacancy = HyperlinkedRelatedField(view_name='api:participants-detail', read_only=True)
    applicant = HyperlinkedRelatedField(view_name='api:users-detail', read_only=True)

    class Meta:
        model = Participant
        fields = ['id', 'vacancy', 'applicant']


class ApplicationWriteOnlySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Participant
        fields = ['vacancy', 'applicant']
