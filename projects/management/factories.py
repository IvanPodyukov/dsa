import factory.django
import datetime

from account.models import User
from participants.models import Participant

from projects.management.providers import RussiaPhoneNumberProvider, ProjectNameProvider, UserDescriptionProvider
from projects.management.utils import generate_phrase
from projects.models import Project

factory.Faker.add_provider(RussiaPhoneNumberProvider)
factory.Faker.add_provider(ProjectNameProvider)
factory.Faker.add_provider(UserDescriptionProvider)


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    email = factory.Faker('email')
    full_name = factory.Faker('name', locale='ru_RU')
    description = factory.Faker('user_description')
    phone = factory.Faker('russia_phone_number')
    avatar = factory.Faker('image_url')
    is_staff = True
    password = '12345'

    @factory.post_generation
    def interests(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.interests.add(*extracted)


class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    title = factory.Faker('project_name')
    creator = factory.Faker('random_element', elements=User.objects.all())
    description = factory.LazyAttribute(lambda x: f'{generate_phrase("", 200)}')
    created = factory.Faker('date_between_dates',
                            date_start=datetime.date(2023, 1, 1),
                            date_end=datetime.date.today())
    application_deadline = factory.Faker('date_between_dates',
                                         date_start=factory.SelfAttribute('..created'),
                                         date_end=factory.LazyAttribute(
                                             lambda x: x.factory_parent.created + datetime.timedelta(
                                                 weeks=10)))
    completion_deadline = factory.Faker('date_between_dates',
                                        date_start=factory.SelfAttribute('..application_deadline'),
                                        date_end=factory.LazyAttribute(
                                            lambda x: x.factory_parent.application_deadline + datetime.timedelta(
                                                weeks=40)))

    @factory.post_generation
    def tags(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        self.tags.add(*extracted)


class ParticipantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Participant

    title = factory.Faker('job', locale='ru_RU')
    description = factory.LazyAttribute(lambda x: generate_phrase('', 100))
