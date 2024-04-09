from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User

from notifications.models import Notification


class NotificationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user1 = User.objects.create_user(email='vlad1@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan1@vk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def test_notifications_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('notifications:notifications_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_notifications_list_unauthorized(self):
        url = reverse('notifications:notifications_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_notification_read_authorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:read_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        notification.refresh_from_db()
        self.assertFalse(notification.unread)
        self.client.logout()
        notification.delete()

    def test_notification_read_unauthorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1)
        url = reverse('notifications:read_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        notification.delete()

    def test_notification_read_another_user(self):
        notification = Notification.objects.create(text='Aaa', user=self.user2)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:read_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        notification.delete()

    def test_notification_unread_authorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1, unread=False)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:unread_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        notification.refresh_from_db()
        self.assertTrue(notification.unread)
        self.client.logout()
        notification.delete()

    def test_notification_unread_unauthorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1, unread=False)
        url = reverse('notifications:unread_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        notification.delete()

    def test_notification_unread_another_user(self):
        notification = Notification.objects.create(text='Aaa', user=self.user2, unread=False)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:unread_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        notification.delete()

    def test_notification_clear_authorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:clear_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        self.assertEqual(0, self.user1.notifications.count())
        self.client.logout()
        notification.delete()

    def test_notification_clear_unauthorized(self):
        notification = Notification.objects.create(text='Aaa', user=self.user1)
        url = reverse('notifications:clear_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        notification.delete()

    def test_notification_clear_another_user(self):
        notification = Notification.objects.create(text='Aaa', user=self.user2)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:clear_notification', args=(notification.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        notification.delete()

    def test_notifications_read_all_authorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:read_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        notification1.refresh_from_db()
        self.assertFalse(notification1.unread)
        notification2.refresh_from_db()
        self.assertFalse(notification2.unread)
        self.client.logout()
        self.user1.notifications.all().delete()

    def test_notifications_read_all_unauthorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1)
        url = reverse('notifications:read_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        self.user1.notifications.all().delete()

    def test_notifications_unread_all_authorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1, unread=False)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1, unread=False)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:unread_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        notification1.refresh_from_db()
        self.assertTrue(notification1.unread)
        notification2.refresh_from_db()
        self.assertTrue(notification2.unread)
        self.client.logout()
        self.user1.notifications.all().delete()

    def test_notifications_unread_all_unauthorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1, unread=False)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1, unread=False)
        url = reverse('notifications:unread_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        self.user1.notifications.all().delete()

    def test_notifications_clear_all_authorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1)
        self.client.login(email=self.user1.email)
        url = reverse('notifications:clear_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('notifications:notifications_list'))
        self.assertEqual(0, self.user1.notifications.count())
        self.client.logout()

    def test_notifications_clear_all_unauthorized(self):
        notification1 = Notification.objects.create(text='Aaa', user=self.user1)
        notification2 = Notification.objects.create(text='Aaa1', user=self.user1)
        url = reverse('notifications:clear_all_notifications')
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        self.user1.notifications.all().delete()

    @classmethod
    def tearDownClass(cls):
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
