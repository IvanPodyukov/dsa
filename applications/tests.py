import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User
from applications.models import Application
from participants.models import Participant
from projects.models import Project


class ApplicationTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user1 = User.objects.create_user(email='vlad1@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan1@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1
        cls.project_info = {
            'title': 'Title', 'description': 'Desc',
            'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
            'completion_deadline': datetime.date.today() + datetime.timedelta(days=3),
            'creator': cls.user1
        }
        cls.participant_info = {
            'title': 'Role1',
            'description': 'Role1Desc'
        }

    def test_applications_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('applications:applications_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_applications_list_unauthorized(self):
        url = reverse('applications:applications_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_application_accept_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        url = reverse('applications:application_accept', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_application_accept_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        url = reverse('applications:application_accept', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('projects:participants_list', args=(project.pk,)))
        self.assertFalse(Application.objects.filter(vacancy=participant, applicant=self.user2).exists())
        participant.refresh_from_db()
        self.assertEqual(participant.participant, self.user2)
        self.assertEqual(participant.applications.all().count(), 0)
        self.client.logout()
        project.delete()

    def test_application_accept_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        url = reverse('applications:application_accept', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    def test_application_reject_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        url = reverse('applications:application_reject', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_application_reject_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        url = reverse('applications:application_reject', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('participants:participant_applications_list',
                                               args=(participant.pk,)))
        self.assertFalse(Application.objects.filter(vacancy=participant, applicant=self.user2).exists())
        self.client.logout()
        project.delete()

    def test_application_reject_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        url = reverse('applications:application_reject', args=(application.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
