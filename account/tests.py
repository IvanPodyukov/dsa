from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User, Interest


class UserTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interest = Interest.objects.create(title='Math')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def test_logout_authorized(self):
        self.client.login(email=self.user1.email)
        response = self.client.post(reverse('account:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main'))

    def test_logout_unauthorized(self):
        url = reverse('account:logout')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_profile_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('account:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_profile_unauthorized(self):
        url = reverse('account:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_user_detail_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('account:user-detail', args=(self.user2.pk, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_user_detail_unauthorized(self):
        url = reverse('account:user-detail', args=(self.user2.pk, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_user_profile_update_unauthorized(self):
        url = reverse('account:profile_update')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_user_profile_update_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('account:profile_update')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, {'phone': '98765', 'interests': [1]})
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:profile'))
        self.user1.refresh_from_db()
        self.assertEqual('98765', self.user1.phone)
        self.assertEqual([self.interest], list(self.user1.interests.all()))
        self.client.logout()

    @classmethod
    def tearDownClass(cls):
        cls.interest.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
