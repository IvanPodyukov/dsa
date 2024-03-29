from django import template

register = template.Library()


@register.simple_tag
def unreadNotifications(user):
    return user.notifications.filter(unread=True).count()
