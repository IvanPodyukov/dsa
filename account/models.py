from django.conf import settings
from django.conf.global_settings import MEDIA_URL
from django.contrib.auth.models import User
from django.db import models


class Interest(models.Model):
    title = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.title


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', null=True)
    phone = models.CharField(max_length=15)
    cv = models.FileField(upload_to='cv/%Y/%m/%d')
    interests = models.ManyToManyField(Interest, related_name='interested_users')

    def __str__(self):
        return self.user.username

    def get_absolute_file_upload_url(self):
        return MEDIA_URL + self.cv.url
