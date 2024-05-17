import random

from django.core.management.base import BaseCommand, CommandError

from account.models import User
from applications.models import Application
from participants.models import Participant


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('k', type=int, help='Число заявок')

    def handle(self, *args, **options):
        k = options['k']
        if not (1 <= k <= 10000):
            raise CommandError('Значение k должно быть между 1 и 10000')
        participants = Participant.objects.filter(participant=None)
        users = User.objects.all()
        for _ in range(k):
            participant = random.choice(participants)
            user = random.choice(users)
            while Application.objects.filter(vacancy=participant, applicant=user).exists():
                participant = random.choice(participants)
                user = random.choice(users)
            Application.objects.create(vacancy=participant, applicant=user)
        self.stdout.write(self.style.SUCCESS(f'Generated {k} applications'))
