from django.db import models

from account.models import User
from projects.models import Project


class Participant(models.Model):
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name='participants')
    participant = models.ForeignKey(User,
                                    on_delete=models.CASCADE,
                                    related_name='participations',
                                    null=True)
