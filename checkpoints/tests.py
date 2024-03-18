from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User


class CheckpointTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(email='vlad@vk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user

    def test_checkpoints_list_authorized(self):
        self.client.login(email=self.user.email)
        url = reverse('checkpoints:checkpoints_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_checkpoints_list_unauthorized(self):
        url = reverse('checkpoints:checkpoints_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    @classmethod
    def tearDownClass(cls):
        cls.user.delete()
        cls.mock_authenticate.stop()