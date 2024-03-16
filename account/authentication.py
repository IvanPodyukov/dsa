import requests
from django.contrib.auth.backends import BaseBackend

from account.models import User


class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None):
        try:
            user = User.objects.get(email=email)
            response = requests.post('https://auth.hse.ru/adfs/oauth2/token', data={
                'username': email,
                'password': password,
                'client_id': '40be8ab1-afde-4635-85d8-4cb834d88594',
                'grant_type': 'password'
            }, verify=False)
            if response.status_code == 400:
                return None
            return user
        except User.DoesNotExist:
            response = requests.post('https://auth.hse.ru/adfs/oauth2/token', data={
                'username': email,
                'password': password,
                'client_id': '40be8ab1-afde-4635-85d8-4cb834d88594',
                'grant_type': 'password'
            }, verify=False)
            if response.status_code == 400:
                return None
            token = response.json()['access_token']
            response = requests.get('https://api.hseapp.ru/v3/dump/me',
                                    headers={'Authorization': f'Bearer {token}'}).json()
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
