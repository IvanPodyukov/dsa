from django import template

from projects.models import Project

register = template.Library()


@register.simple_tag
def commonInterests(project, user):
    return project.tags.filter(interested_users=user)


@register.simple_tag
def isUserAllowToViewParticipants(project, user):
    return project.creator == user or project.participants.filter(participant=user).exists()
