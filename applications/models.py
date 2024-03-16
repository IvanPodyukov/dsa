from django.conf import settings
from django.db import models

from account.models import User
from projects.models import Participant


class Application(models.Model):
    '''
    SUBMITTED = "SU"
    ACCEPTED = "AC"
    REJECTED = "RE"

    STATUS_CHOICES = (
        (SUBMITTED, "НА РАССМОТРЕНИИ"),
        (ACCEPTED, "ОДОБРЕНА"),
        (REJECTED, "ОТКЛОНЕНА"),
    )
    '''

    vacancy = models.ForeignKey(Participant,
                                on_delete=models.CASCADE,
                                related_name='applications')
    applicant = models.ForeignKey(User,
                                  on_delete=models.CASCADE,
                                  related_name='applications')
    created = models.DateTimeField(auto_now_add=True)
    # status = models.CharField(max_length=2, choices=STATUS_CHOICES, default=SUBMITTED)

    custom_id = models.IntegerField(null=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.custom_id = self.vacancy.applications_num
            self.vacancy.applications_num += 1
            self.vacancy.save()
        super().save(*args, **kwargs)
