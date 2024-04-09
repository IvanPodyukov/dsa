import datetime
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User, Interest
from applications.models import Application
from participants.models import Participant
from projects.models import Project


class ParticipantTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interest = Interest.objects.create(title='Math')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
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

    def test_my_participations_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('participants:my_participations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_my_participations_list_unauthorized(self):
        url = reverse('participants:my_participations')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_participant_submit_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_submit', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        self.assertTrue(Application.objects.filter(vacancy=participant, applicant=self.user1).exists())
        self.client.logout()
        project.delete()

    def test_participant_submit_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_submit', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_participant_withdraw_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        Application.objects.create(applicant=self.user1, vacancy=participant)
        url = reverse('participants:participant_withdraw', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        self.assertFalse(Application.objects.filter(vacancy=participant, applicant=self.user1).exists())
        self.client.logout()
        project.delete()

    def test_participant_withdraw_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        Application.objects.create(applicant=self.user1, vacancy=participant)
        url = reverse('participants:participant_withdraw', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_applications_list_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_applications_list', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_applications_list_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_applications_list', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        project.delete()

    def test_applications_list_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_applications_list', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    def test_participant_confirm_clear_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user1)
        url = reverse('participants:confirm_clear_participant', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_participant_confirm_clear_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user1)
        url = reverse('participants:confirm_clear_participant', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        project.delete()

    def test_participant_confirm_clear_not_creator_or_participant(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user2)
        url = reverse('participants:confirm_clear_participant', args=(participant.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    def test_participant_clear_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user1)
        url = reverse('participants:clear_participant', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_participant_clear_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user2)
        url = reverse('participants:clear_participant', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('projects:project_info', args=(project.pk,)))
        participant.refresh_from_db()
        self.assertTrue(self.user2.notifications.filter(
            text=f'Вы были удалены с роли {participant.title} в проекте {project.title}').exists())
        self.assertIsNone(participant.participant)
        self.client.logout()
        project.delete()

    def test_participant_clear_not_creator_or_participant(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user2)
        url = reverse('participants:clear_participant', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.interest.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
