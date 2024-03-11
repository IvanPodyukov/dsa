from django import template


register = template.Library()

@register.simple_tag
def commonInterests(project, user):
    return project.tags.filter(interested_users=user.profile)