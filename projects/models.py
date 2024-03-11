from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from account.models import Interest


class Project(models.Model):
    ACTIVE = "AC"
    COMPLETED = "CO"
    VACANT = "VA"

    STATUS_CHOICES = (
        (ACTIVE, "АКТИВНЫЙ"),
        (COMPLETED, "ЗАВЕРШЕН"),
        (VACANT, "ЕСТЬ ВАКАНСИИ"),
    )

    title = models.CharField(max_length=50)
    creator = models.ForeignKey(User,
                                on_delete=models.CASCADE,
                                related_name='created_projects')
    description = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    application_deadline = models.DateField()
    completion_deadline = models.DateField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=VACANT)
    tags = models.ManyToManyField(Interest, related_name='projects')
    checkpoints_num = models.IntegerField(default=1)
    participants_num = models.IntegerField(default=1)

    def number_of_participants(self):
        return self.participants.count()

    def number_of_vacancies(self):
        return self.participants.filter(participant=None).count()


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
    custom_id = models.IntegerField(null=True)
    applications_num = models.IntegerField(default=1)

    def save(self, *args, **kwargs):
        if not self.id:
            self.custom_id = self.project.participants_num
            self.project.participants_num += 1
            self.project.save()
        super().save(*args, **kwargs)
