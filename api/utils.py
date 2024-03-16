from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from account.models import User


def get_and_authenticate_user(email, password):
    user = authenticate(email=email, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid username/password. Please try again!")
    return user
