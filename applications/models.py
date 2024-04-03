from django.conf import settings
from django.db import models

from account.models import User
from participants.models import Participant


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
