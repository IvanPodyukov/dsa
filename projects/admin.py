from django.contrib import admin
from django.contrib.auth.models import User

from checkpoints.models import Checkpoint
from projects.models import Project, Participant


class CheckpointInline(admin.StackedInline):
    model = Checkpoint


class ParticipantInline(admin.StackedInline):
    model = Participant


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [CheckpointInline, ParticipantInline]
