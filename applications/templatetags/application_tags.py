from django import template

from applications.models import Application

register = template.Library()


@register.simple_tag
def applicationExists(vacancy, applicant):
    return Application.objects.filter(vacancy=vacancy, applicant=applicant).exists()

