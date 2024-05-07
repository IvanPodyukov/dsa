import random

from faker import Faker
from faker.providers.phone_number import Provider


class RussiaPhoneNumberProvider(Provider):
    def russia_phone_number(self):
        return f'+7 {self.msisdn()[3:]}'


class ProjectNameProvider(Provider):
    project_keywords = ['Система', 'Разработка', 'Платформа', 'Исследование', 'Анализ', 'Прототип', 'Сервис',
                        'Организация', 'Сопровождение', 'Решение', 'Экспедиция', 'Стажировка']
    fake = Faker('ru_RU')

    def project_name(self):
        project_name = f'{random.choice(self.project_keywords)} "{self.fake.catch_phrase()}"'
        return project_name


class UserDescriptionProvider(Provider):
    def user_description(self):
        return f'Бакалавриат БПИ2{random.randint(0, 3)}{random.randint(1, 7)}'
