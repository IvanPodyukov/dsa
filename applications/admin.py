from django.contrib import admin

from applications.models import Application
from projects.models import Participant


class ApplicationInline(admin.StackedInline):
    model = Application


@admin.register(Participant)
class ParticipantAdmin(admin.ModelAdmin):
    inlines = [ApplicationInline]


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    pass
