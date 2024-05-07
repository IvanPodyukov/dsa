import datetime
import random

from faker import Faker

fake = Faker('ru_RU')


def generate_phrase(first, max_length):
    res = first + fake.catch_phrase()
    while len(res) > max_length:
        res = first + fake.catch_phrase()
    return res


def random_date(start, end, i):
    return start + datetime.timedelta(
        days=random.randint(1, max(1, (end - start - datetime.timedelta(i)).days)))
