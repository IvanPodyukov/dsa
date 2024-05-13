import random

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from account.models import Interest
from projects.management.factories import UserFactory


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('k', type=int, help='Число пользователей')

    def handle(self, *args, **options):
        k = options['k']
        if not (1 <= k <= 500):
            raise CommandError('Значение k должно быть между 1 и 500')
        interests = Interest.objects.all()
        for _ in range(k):
            try:
                UserFactory.create(interests=random.choices(interests, k=random.randint(1, 4)))
            except IntegrityError:
                continue
        self.stdout.write(self.style.SUCCESS(f'Generated {k} users'))
