from django.db import models

from projects.models import Project


# Create your models here.

class Checkpoint(models.Model):
    title = models.CharField(max_length=30)
    description = models.CharField(max_length=100)
    deadline = models.DateField()
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name='checkpoints')
