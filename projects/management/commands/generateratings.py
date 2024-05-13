import random

from django.core.management.base import BaseCommand, CommandError

from account.models import User
from projects.models import Project, Rating


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('k', type=int, help='Число рейтингов')

    def handle(self, *args, **options):
        k = options['k']
        if not (1 <= k <= 10000):
            raise CommandError('Значение k должно быть между 1 и 10000')
        projects = Project.objects.all()
        users = User.objects.all()
        for _ in range(k):
            is_good_rating = random.choice([True, False])
            if is_good_rating:
                rating = random.randint(4, 5)
            else:
                is_not_zero = random.randint(0, 7)
                if is_not_zero > 0:
                    rating = random.randint(1, 3)
                else:
                    rating = 0
            project = random.choice(projects)
            user = random.choice(users)
            while Rating.objects.filter(project=project, user=user).exists():
                project = random.choice(projects)
                user = random.choice(users)
            Rating.objects.create(project=project, user=user,
                                  rating=rating)
        self.stdout.write(self.style.SUCCESS(f'Generated {k} ratings'))
