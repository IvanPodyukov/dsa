from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from account.models import User, Interest
from api.serializers import ProjectUpdateSerializer
from applications.models import Application
from participants.models import Participant
from projects.models import Project


class ProjectTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.interest = Interest.objects.create(title='Math')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1
        cls.project_info = {
            'title': 'Title', 'description': 'Desc',
            'application_deadline': '2024-04-05',
            'completion_deadline': '2024-04-07',
            'creator': cls.user1
        }
        cls.participant_info = {
            'title': 'Role1',
            'description': 'Role1Desc'
        }

    def test_project_create_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('projects:project_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        csrf_token = response.cookies['csrftoken'].value
        project_info = {
            'csrfmiddlewaretoken': csrf_token, 'title': 'Title', 'description': 'Desc',
            'application_deadline': '2024-04-05',
            'completion_deadline': '2024-04-07', 'tags': [1], 'checkpoints-TOTAL_FORMS': '1',
            'checkpoints-INITIAL_FORMS': '0', 'checkpoints-MIN_NUM_FORMS': '0',
            'checkpoints-MAX_NUM_FORMS': '1000', 'checkpoints-0-title': '', 'checkpoints-0-description': '',
            'checkpoints-0-deadline': '', 'checkpoints-0-DELETE': 'on', 'checkpoints-0-id': '',
            'checkpoints-0-project': '', 'participants-TOTAL_FORMS': '1', 'participants-INITIAL_FORMS': '0',
            'participants-MIN_NUM_FORMS': '0', 'participants-MAX_NUM_FORMS': '1000',
            'participants-0-title': 'Role1',
            'participants-0-description': 'RoleDesc1', 'participants-0-id': '', 'participants-0-project': ''
        }
        response = self.client.post(url, project_info)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_project_create_unauthorized(self):
        url = reverse('projects:project_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_project_detail_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:project_info', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        project.delete()

    def test_project_detail_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:project_info', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_project_update_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        data = ProjectUpdateSerializer(project).data
        data['description'] = 'new'
        url = reverse('projects:project_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('projects:project_info', args=(project.pk,)))
        self.client.logout()
        project.delete()

    def test_project_update_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        project.creator = self.user2
        url = reverse('projects:project_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        project.delete()

    def test_project_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:project_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_project_submit_authorized(self):
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

    def test_project_submit_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        url = reverse('participants:participant_submit', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_project_withdraw_authorized(self):
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

    def test_project_withdraw_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(**self.participant_info, project=project)
        Application.objects.create(applicant=self.user1, vacancy=participant)
        url = reverse('participants:participant_withdraw', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_participants_list_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:participants_list', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_participants_list_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:participants_list', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        project.delete()

    def test_participants_list_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        url = reverse('projects:participants_list', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
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
        participant = Participant.objects.create(**self.participant_info, project=project, participant=self.user1)
        url = reverse('participants:clear_participant', args=(participant.pk,))
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('projects:project_info', args=(project.pk,)))
        participant.refresh_from_db()
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

    def test_project_delete_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:delete_project', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_project_delete_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:delete_project', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('projects:my_projects_list'))
        self.assertFalse(Project.objects.filter(**self.project_info).exists())
        self.client.logout()
        project.delete()

    def test_project_delete_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        url = reverse('projects:delete_project', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    def test_checkpoint_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:checkpoints_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)
        project.delete()

    def test_checkpoint_update_authorized(self):
        self.client.login(email=self.user1.email)
        project = Project.objects.create(**self.project_info)
        url = reverse('projects:checkpoints_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        checkpoint_info = {
            'csrfmiddlewaretoken': response.cookies['csrftoken'].value,
            'checkpoints-TOTAL_FORMS': 1, 'checkpoints-INITIAL_FORMS': 0, 'checkpoints-MIN_NUM_FORMS': 0,
            'checkpoints-MAX_NUM_FORMS': 1000, 'checkpoints-0-title': 'Check1',
            'checkpoints-0-description': 'DescCheck1', 'checkpoints-0-deadline': '2024-04-06', 'checkpoints-0-id': '',
            'checkpoints-0-project': 2
        }
        response = self.client.post(url, data=checkpoint_info)
        self.assertEqual(response.status_code, 200)
        self.client.logout()
        project.delete()

    def test_checkpoint_update_not_creator(self):
        self.client.login(email=self.user1.email)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        url = reverse('projects:checkpoints_update', args=(project.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)
        self.client.logout()
        project.delete()

    def test_projects_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('projects:projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_projects_list_unauthorized(self):
        url = reverse('projects:projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_recommended_projects_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('projects:recommended_projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_recommended_projects_list_unauthorized(self):
        url = reverse('projects:recommended_projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    def test_my_projects_list_authorized(self):
        self.client.login(email=self.user1.email)
        url = reverse('projects:my_projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

    def test_my_projects_list_unauthorized(self):
        url = reverse('projects:my_projects_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('account:login') + '?next=' + url)

    @classmethod
    def tearDownClass(cls):
        cls.interest.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
