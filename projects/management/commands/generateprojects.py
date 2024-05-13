import random
import datetime

from django.core.management.base import BaseCommand, CommandError
from faker import Faker

from account.models import Interest, User
from checkpoints.models import Checkpoint
from projects.management.factories import ProjectFactory, ParticipantFactory
from projects.management.utils import random_date, generate_phrase
from projects.models import Project


class Command(BaseCommand):
    fake = Faker('ru_RU')

    def _update_project(self, project):
        project.created = random_date(project.application_deadline - datetime.timedelta(weeks=10),
                                      project.application_deadline, 1)
        if project.completion_deadline < datetime.date.today():
            project.status = Project.COMPLETED
        elif all(participant.participant is not None for participant in project.participants.all()):
            project.status = Project.ACTIVE
        project.save()

    def _create_checkpoint(self, last_deadline, project, checkpoints_num, i):
        deadline = random_date(last_deadline, project.completion_deadline, checkpoints_num - i)
        checkpoint = Checkpoint.objects.create(project=project, title=f'Контрольная точка {i + 1}',
                                               description=generate_phrase('', 100),
                                               deadline=deadline)
        return checkpoint

    def _create_participant(self, project, users):
        participant = ParticipantFactory.build(project=project)
        if random.random() > 0.5:
            participant.participant = random.choice(users)
        while len(participant.title) > 30:
            participant.title = self.fake.job()
        participant.save()

    def _create_projects(self, interests, users, k):
        for _ in range(k):
            project = ProjectFactory.create(tags=random.choices(interests, k=random.randint(1, 4)))
            checkpoints_num = random.randint(0, 4)
            last_deadline = project.application_deadline
            for i in range(checkpoints_num):
                checkpoint = self._create_checkpoint(last_deadline, project, checkpoints_num, i)
                last_deadline = checkpoint.deadline
            participants_num = random.randint(1, 6)
            for _ in range(participants_num):
                self._create_participant(project, users)
            self._update_project(project)

    def add_arguments(self, parser):
        parser.add_argument('k', type=int, help='Число проектов')

    def handle(self, *args, **options):
        k = options['k']
        if not (1 <= k <= 1000):
            raise CommandError('Значение k должно быть между 1 и 1000')
        interests = Interest.objects.all()
        users = User.objects.all()
        self._create_projects(interests, users, k)
        self.stdout.write(self.style.SUCCESS(f'Generated {k} projects'))
