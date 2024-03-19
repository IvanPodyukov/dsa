import requests
from django.contrib.auth.backends import BaseBackend
from rest_framework import HTTP_HEADER_ENCODING, exceptions
from rest_framework.authentication import TokenAuthentication
from django.utils.translation import gettext_lazy as _

from account.models import User


class EmailAuthBackend(BaseBackend):

    def get_token(self, email, password):
        return requests.post('https://auth.hse.ru/adfs/oauth2/token', data={
            'username': email,
            'password': password,
            'client_id': '40be8ab1-afde-4635-85d8-4cb834d88594',
            'grant_type': 'password'
        }, verify=False)

    def get_user_json(self, token):
        return requests.get('https://api.hseapp.ru/v3/dump/me',
                            headers={'Authorization': f'Bearer {token}'}).json()

    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            response = self.get_token(email, password)
            if response.status_code == 400:
                return None
            token = response.json()['access_token']
            response = self.get_user_json(token)
            user.description = response['description']
            user.full_name = response['full_name']
            user.avatar = response.get('avatar_url', None)
            user.save()
            return user
        except User.DoesNotExist:
            response = self.get_token(email, password)
            if response.status_code == 400:
                return None
            token = response.json()['access_token']
            response = self.get_user_json(token)
            user = User.objects.create(email=email,
                                       password=password,
                                       description=response['description'],
                                       full_name=response['full_name'])
            return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

    def authenticate_header(self, request):
        pass


class HSETokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        auth = request.META.get('HTTP_HSE_AUTH', b'')
        if isinstance(auth, str):
            auth = auth.encode(HTTP_HEADER_ENCODING)

        auth = auth.split()
        if not auth:
            return None
        elif len(auth) > 1:
            msg = _('Invalid token header. Token string should not contain spaces.')
            raise exceptions.AuthenticationFailed(msg)

        try:
            token = auth[0].decode()
        except UnicodeError:
            msg = _('Invalid token header. Token string should not contain invalid characters.')
            raise exceptions.AuthenticationFailed(msg)

        return self.authenticate_credentials(token)