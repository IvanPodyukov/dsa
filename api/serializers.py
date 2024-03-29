import datetime

from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.fields import SerializerMethodField, CharField, FileField

from account.models import Interest, User
from applications.models import Application
from checkpoints.models import Checkpoint
from notifications.models import Notification
from projects.models import Project, Participant


class InterestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ['id', 'title']


class UserInfoSerializer(serializers.ModelSerializer):
    interests = InterestSerializer(many=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'description', 'email', 'phone', 'cv', 'interests', 'avatar']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone', 'cv', 'interests']


class UserLoginSerializer(serializers.Serializer):
    email = CharField(max_length=50, required=True)
    password = CharField(required=True, write_only=True)


class AuthUserSerializer(serializers.ModelSerializer):
    auth_token = SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'description', 'email', 'auth_token']
        read_only_fields = ['id']

    def get_auth_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key


class CheckpointReadOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['id', 'project', 'title', 'description', 'deadline']


class CheckpointCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['title', 'description', 'deadline']


class CheckpointUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Checkpoint
        fields = ['title', 'description']


class ParticipantSerializer(serializers.ModelSerializer):
    participant = SerializerMethodField()

    class Meta:
        model = Participant
        fields = ['id', 'project', 'title', 'description', 'participant']
        read_only_fields = ['project']

    def get_participant(self, obj):
        participants_and_creator = set(x.participant for x in obj.project.participants.all())
        participants_and_creator.add(obj.project.creator)
        if self.context['request'].user in participants_and_creator:
            if obj.participant is None:
                return None
            return obj.participant.pk
        if obj.participant is None:
            return 'Нет участника'
        return 'Есть участник'


class ProjectReadOnlySerializer(serializers.ModelSerializer):
    tags = InterestSerializer(many=True, read_only=True)
    vacancies_num = SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'creator', 'created', 'description', 'application_deadline', 'completion_deadline',
                  'status', 'tags', 'checkpoints_num', 'participants_num', 'vacancies_num']

    def get_vacancies_num(self, obj):
        return obj.participants.all().filter(participant=None).count()


class ProjectRecommendedSerializer(serializers.ModelSerializer):
    tags = InterestSerializer(many=True, read_only=True)
    common_tags = SerializerMethodField()
    vacancies_num = SerializerMethodField()

    class Meta:
        model = Project
        fields = ['id', 'title', 'created', 'description', 'application_deadline', 'completion_deadline',
                  'status', 'tags', 'common_tags', 'checkpoints_num', 'participants_num', 'vacancies_num']

    def get_common_tags(self, obj):
        return obj.common_tags

    def get_vacancies_num(self, obj):
        return obj.number_of_vacancies


class ProjectCreateSerializer(serializers.ModelSerializer):
    checkpoints = CheckpointCreateSerializer(many=True)
    participants = ParticipantSerializer(many=True)

    class Meta:
        model = Project
        fields = ['title', 'description', 'application_deadline', 'completion_deadline', 'checkpoints',
                  'participants', 'tags']

    def validate_participants(self, value):
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
        if self.instance.application_deadline != application_deadline and datetime.date.today() >= application_deadline:
            raise serializers.ValidationError('Дедлайн подачи заявки не может быть раньше сегодняшнего дня')
        checkpoints = data.get('checkpoints',
                               [{'deadline': checkpoint.deadline} for checkpoint in self.instance.checkpoints.all()])
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
            instance.checkpoints_num = 0
            checkpoints_data = validated_data.pop('checkpoints')
            for checkpoint_data in checkpoints_data:
                Checkpoint.objects.create(project=instance, **checkpoint_data)
        if 'tags' in validated_data:
            tags_ids = validated_data.pop('tags')
            instance.tags.set(tags_ids)
        super().update(instance, validated_data)
        return instance


class ApplicationReadOnlySerializer(serializers.ModelSerializer):
    vacancy = ParticipantSerializer()
    applicant = UserInfoSerializer()

    class Meta:
        model = Application
        fields = ['id', 'vacancy', 'applicant']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'text', 'unread', 'timestamp']
