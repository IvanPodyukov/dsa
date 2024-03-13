from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from account.models import Profile


def get_and_authenticate_user(email, password):
    user = authenticate(username=email, password=password)
    if user is None:
        raise serializers.ValidationError("Invalid username/password. Please try again!")
    return user


def create_user_account(**data):
    cv = data.pop('cv')
    interests = data.pop('interests')
    phone = data.pop('phone')
    user = get_user_model().objects.create_user(**data)
    profile = Profile.objects.create(user=user, cv=cv, phone=phone)
    profile.interests.set(interests)
    return user
