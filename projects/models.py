from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator

from django.db import models
from django.db.models import Avg
from django.urls import reverse

from account.models import Interest, User


class Project(models.Model):
    ACTIVE = "AC"
    COMPLETED = "CO"
    VACANT = "VA"

    STATUS_CHOICES = (
        (ACTIVE, "АКТИВНЫЙ"),
        (COMPLETED, "ЗАВЕРШЕН"),
        (VACANT, "ЕСТЬ ВАКАНСИИ"),
    )

    title = models.CharField(max_length=100)
    creator = models.ForeignKey(User,
                                on_delete=models.CASCADE,
                                related_name='created_projects')
    description = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    application_deadline = models.DateField()
    completion_deadline = models.DateField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=VACANT)
    tags = models.ManyToManyField(Interest, related_name='projects')

    def mean_rating(self):
        return self.ratings.all().aggregate(mean_rating=Avg('rating'))['mean_rating']

    def get_absolute_url(self):
        return reverse('projects:project_info', args=(self.id,))

    def get_vacancies(self):
        vacancies = self.participants.filter(participant=None)
        if vacancies.count() == 0:
            return '—'
        return ', '.join(vacancy.title for vacancy in vacancies)


class Rating(models.Model):
    project = models.ForeignKey(Project,
                                on_delete=models.CASCADE,
                                related_name='ratings')
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='ratings')
    rating = models.PositiveSmallIntegerField(validators=[
        MaxValueValidator(5),
        MinValueValidator(0)
    ])
