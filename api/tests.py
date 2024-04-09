import datetime
from unittest.mock import patch

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from account.models import User, Interest
from applications.models import Application
from checkpoints.models import Checkpoint
from notifications.models import Notification
from participants.models import Participant
from projects.models import Project


class UserApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest = Interest.objects.create(title='Math')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_login(self):
        response = self.client.post('/api/users/login/', {'email': self.user1.email, 'password': '1243'}, format='json')
        data = response.json()
        self.assertEqual(['id', 'full_name', 'description', 'email', 'auth_token'], list(data.keys()))
        self.assertEqual(data['id'], self.user1.id)
        self.assertEqual(data['email'], self.user1.email)
        self.assertIn('full_name', data)
        self.assertIn('description', data)

    def test_api_profile_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get('/api/users/profile/', format='json')
        data = response.json()
        self.assertEqual(['id', 'full_name', 'description', 'email', 'phone', 'cv', 'interests', 'avatar'],
                         list(data.keys()))
        self.assertEqual(data['id'], self.user1.id)
        self.assertEqual(data['email'], self.user1.email)
        self.client.credentials()

    def test_api_profile_unauthorized(self):
        response = self.client.get('/api/users/profile/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_user_detail_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get(f'/api/users/{self.user2.pk}/', format='json')
        data = response.json()
        self.assertEqual(['id', 'full_name', 'description', 'email', 'phone', 'cv', 'interests', 'avatar'],
                         list(data.keys()))
        self.assertEqual(data['id'], self.user2.id)
        self.assertEqual(data['email'], self.user2.email)
        self.client.credentials()

    def test_api_user_detail_unauthorized(self):
        response = self.client.get(f'/api/users/{self.user2.pk}/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_user_update_patch_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.patch(f'/api/users/{self.user1.pk}/',
                                     {'phone': '0001', 'interests': [self.interest.pk]},
                                     format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        expected = {
            'id': self.user1.pk,
            'phone': '0001',
            'cv': self.user1.cv,
            'interests': [self.interest.pk]
        }
        self.assertDictEqual(data, expected)
        self.client.credentials()

    def test_api_user_update_patch_unauthorized(self):
        response = self.client.patch(f'/api/users/{self.user1.pk}/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_user_update_patch_another_user(self):
        self.set_credentials(self.user1)
        response = self.client.patch(f'/api/users/{self.user2.pk}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()

    def test_api_user_update_put_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.put(f'/api/users/{self.user1.pk}/',
                                   {'phone': '0001', 'interests': [self.interest.pk]},
                                   format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        expected = {
            'id': self.user1.pk,
            'phone': '0001',
            'cv': self.user1.cv,
            'interests': [self.interest.pk]
        }
        self.assertDictEqual(expected, data)
        self.client.credentials()

    def test_api_user_update_put_unauthorized(self):
        response = self.client.put(f'/api/users/{self.user1.pk}/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_user_update_put_another_user(self):
        self.set_credentials(self.user1)
        response = self.client.put(f'/api/users/{self.user2.pk}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()

    @classmethod
    def tearDownClass(cls):
        cls.interest.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class InterestApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest1 = Interest.objects.create(title='Math')
        cls.interest2 = Interest.objects.create(title='Physics')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user1.interests.add(cls.interest1)
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_interests_list_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get('/api/interests/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x['id'] for x in response.json()], [self.interest1.id, self.interest2.id])
        self.client.credentials()

    def test_api_interests_list_unauthorized(self):
        response = self.client.get('/api/interests/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_interests_mine_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get('/api/interests/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x['id'] for x in response.json()], [self.interest1.id])
        self.client.credentials()

    def test_api_interests_mine_unauthorized(self):
        response = self.client.get('/api/interests/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_interest_retrieve_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get(f'/api/interests/{self.interest1.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'id': self.interest1.id, 'title': self.interest1.title}
        self.assertDictEqual(response.json(), expected)
        self.client.credentials()

    def test_api_interest_retrieve_unauthorized(self):
        response = self.client.get(f'/api/interests/{self.interest1.id}/', format='json')
        self.assertEqual(response.status_code, 401)

    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class ProjectApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest1 = Interest.objects.create(title='Math')
        cls.interest2 = Interest.objects.create(title='Physics')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user1.interests.add(cls.interest1)
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.project_info = {
            'title': 'Title1', 'description': 'Desc1',
            'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
            'completion_deadline': datetime.date.today() + datetime.timedelta(days=3),
            'creator': cls.user1
        }
        cls.participant_info = {
            'title': 'Role1',
            'description': 'Role1Desc'
        }
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_project_create_authorized(self):
        self.set_credentials(self.user1)
        data = {'title': 'Title1', 'description': 'Desc1',
                'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
                'completion_deadline': datetime.date.today() + datetime.timedelta(days=3), 'checkpoints': [],
                'participants': [{'title': 'Part1', 'description': 'PartDesc1'}], 'tags': [self.interest1.id]}
        response = self.client.post('/api/projects/', data=data, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Project.objects.filter(title='Title1'))
        project = Project.objects.get(title='Title1')
        project.delete()
        self.client.credentials()

    def test_api_project_create_unauthorized(self):
        response = self.client.post('/api/projects/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_project_retrieve_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        project.tags.add(self.interest1)
        response = self.client.get(f'/api/projects/{project.pk}/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'id': project.pk, 'title': project.title, 'creator': project.creator.pk,
                    'created': str(project.created),
                    'description': project.description,
                    'application_deadline': str(project.application_deadline),
                    'completion_deadline': str(project.completion_deadline), 'status': project.status,
                    'tags': [{'id': self.interest1.id, 'title': self.interest1.title}], 'checkpoints_num': 0,
                    'participants_num': 0, 'vacancies_num': 0}
        self.assertDictEqual(response.json(), expected)
        project.delete()
        self.client.credentials()

    def test_api_project_retrieve_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        response = self.client.get(f'/api/projects/{project.pk}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_projects_list_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get('/api/projects/', format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        self.client.credentials()

    def test_api_projects_list_unauthorized(self):
        response = self.client.get('/api/projects/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_projects_recommended_authorized(self):
        self.set_credentials(self.user1)
        response = self.client.get('/api/projects/recommended/', format='json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('results', data)
        self.client.credentials()

    def test_api_projects_recommended_unauthorized(self):
        response = self.client.get('/api/projects/recommended/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_projects_mine_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        response = self.client.get('/api/projects/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x['id'] for x in response.json()], [project.id])
        project.delete()
        self.client.credentials()

    def test_api_projects_mine_unauthorized(self):
        response = self.client.get('/api/projects/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_projects_involved_authorized(self):
        self.set_credentials(self.user2)
        project = Project.objects.create(**self.project_info)
        Participant.objects.create(**self.participant_info, project=project, participant=self.user2)
        response = self.client.get('/api/projects/involved/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual([x['id'] for x in response.json()], [project.id])
        project.delete()
        self.client.credentials()

    def test_api_projects_involved_unauthorized(self):
        response = self.client.get('/api/projects/involved/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_project_destroy_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        project.tags.add(self.interest1)
        response = self.client.delete(f'/api/projects/{project.pk}/', format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, self.user1.created_projects.count())
        project.delete()
        self.client.credentials()

    def test_api_project_destroy_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        response = self.client.delete(f'/api/projects/{project.pk}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_project_destroy_another_user(self):
        self.set_credentials(self.user2)
        project = Project.objects.create(**self.project_info)
        response = self.client.delete(f'/api/projects/{project.pk}/', format='json')
        self.assertEqual(response.status_code, 403)
        project.delete()
        self.client.credentials()

    def test_api_project_checkpoints_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        project.tags.add(self.interest1)
        checkpoint = Checkpoint.objects.create(title='df', description='fddf',
                                               deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               project=project)
        response = self.client.get(f'/api/projects/{project.pk}/checkpoints/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = [{'id': checkpoint.pk, 'project': project.pk, 'title': 'df', 'description': 'fddf',
                     'deadline': str(datetime.date.today() + datetime.timedelta(days=2))}]
        self.assertEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_project_checkpoints_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        response = self.client.get(f'/api/projects/{project.pk}/checkpoints/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_project_participants_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        project.tags.add(self.interest1)
        participant = Participant.objects.create(title='df', description='fddf', project=project)
        response = self.client.get(f'/api/projects/{project.pk}/participants/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = [
            {'id': participant.pk, 'project': project.pk, 'title': 'df', 'description': 'fddf', 'participant': None}]
        self.assertEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_project_participants_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        response = self.client.get(f'/api/projects/{project.pk}/participants/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_project_partial_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        response = self.client.patch(f'/api/projects/{project.pk}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 200)
        project.refresh_from_db()
        self.assertEqual('NEW_TITLE', project.title)
        self.client.credentials()
        project.delete()

    def test_api_project_partial_update_unathorized(self):
        project = Project.objects.create(**self.project_info)
        response = self.client.patch(f'/api/projects/{project.pk}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_project_partial_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        response = self.client.patch(f'/api/projects/{project.pk}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_project_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        data = self.project_info.copy()
        data['creator'] = self.user1.pk
        data['tags'] = [self.interest1.pk]
        data['checkpoints'] = [
            {'title': 'Check1', 'description': 'desc1', 'deadline': datetime.date.today() + datetime.timedelta(days=2)}]
        data['participants'] = [{'title': 'Rl12', 'description': 'This is role'}]
        response = self.client.put(f'/api/projects/{project.pk}/', data=data, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.credentials()
        project.delete()

    def test_api_project_update_unathorized(self):
        project = Project.objects.create(**self.project_info)
        data = self.project_info.copy()
        data['creator'] = self.user1.pk
        data['tags'] = [self.interest1.pk]
        data['checkpoints'] = [
            {'title': 'Check1', 'description': 'desc1', 'deadline': datetime.date.today() + datetime.timedelta(days=2)}]
        data['participants'] = [{'title': 'Rl12', 'description': 'This is role'}]
        response = self.client.put(f'/api/projects/{project.pk}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_project_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        data = new_project_info.copy()
        data['creator'] = self.user1.pk
        data['tags'] = [self.interest1.pk]
        data['checkpoints'] = [
            {'title': 'Check1', 'description': 'desc1', 'deadline': datetime.date.today() + datetime.timedelta(days=2)}]
        data['participants'] = [{'title': 'Rl12', 'description': 'This is role'}]
        response = self.client.put(f'/api/projects/{project.pk}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class CheckpointApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest1 = Interest.objects.create(title='Math')
        cls.interest2 = Interest.objects.create(title='Physics')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user1.interests.add(cls.interest1)
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.project_info = {
            'title': 'Title1', 'description': 'Desc1',
            'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
            'completion_deadline': datetime.date.today() + datetime.timedelta(days=3),
            'creator': cls.user1
        }
        cls.checkpoint_info = {
            'deadline': datetime.date.today() + datetime.timedelta(days=2),
            'title': 'UPDATE_TITLE', 'description': 'UPDATE_DESC'
        }
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_checkpoints_mine_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.get(f'/api/checkpoints/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'count': 1, 'next': None, 'previous': None, 'results': [
            {'id': checkpoint.id, 'project': project.id, 'title': 'Check1', 'description': 'DescCheck1',
             'deadline': str(datetime.date.today() + datetime.timedelta(days=2))}]}
        self.assertDictEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_checkpoints_mine_unauthorized(self):
        response = self.client.get(f'/api/checkpoints/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_checkpoint_retrieve_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        response = self.client.get(f'/api/checkpoints/{checkpoint.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'id': checkpoint.id, 'project': project.id, 'title': 'Check1', 'description': 'DescCheck1',
                    'deadline': str(datetime.date.today() + datetime.timedelta(days=2))}
        self.assertDictEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_checkpoint_retrieve_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        response = self.client.get(f'/api/checkpoints/{checkpoint.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_checkpoint_partial_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        response = self.client.patch(f'/api/checkpoints/{checkpoint.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 200)
        checkpoint.refresh_from_db()
        self.assertEqual('NEW_TITLE', checkpoint.title)
        self.client.credentials()
        project.delete()

    def test_api_checkpoint_partial_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        response = self.client.patch(f'/api/checkpoints/{checkpoint.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_checkpoint_partial_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        response = self.client.patch(f'/api/checkpoints/{checkpoint.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_checkpoint_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        data = self.checkpoint_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/checkpoints/{checkpoint.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 200)
        checkpoint.refresh_from_db()
        self.assertEqual('UPDATE_TITLE', checkpoint.title)
        self.assertEqual('UPDATE_DESC', checkpoint.description)
        self.client.credentials()
        project.delete()

    def test_api_checkpoint_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        data = self.checkpoint_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/checkpoints/{checkpoint.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_checkpoint_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        checkpoint = Checkpoint.objects.create(deadline=datetime.date.today() + datetime.timedelta(days=2),
                                               title='Check1', description='DescCheck1', project=project)
        data = self.checkpoint_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/checkpoints/{checkpoint.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class ParticipantApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest1 = Interest.objects.create(title='Math')
        cls.interest2 = Interest.objects.create(title='Physics')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user1.interests.add(cls.interest1)
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.project_info = {
            'title': 'Title1', 'description': 'Desc1',
            'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
            'completion_deadline': datetime.date.today() + datetime.timedelta(days=3),
            'creator': cls.user1
        }
        cls.participant_info = {
            'title': 'UPDATE_TITLE', 'description': 'UPDATE_DESC'
        }
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_participants_mine_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.get(f'/api/participants/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = [{'id': participant.id, 'project': project.id, 'title': participant.title,
                     'description': participant.description, 'participant': self.user1.pk}]
        self.assertEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_participants_mine_unauthorized(self):
        response = self.client.get(f'/api/participants/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_participant_retrieve_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.get(f'/api/participants/{participant.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'id': participant.id, 'project': project.id, 'title': participant.title,
                    'description': participant.description, 'participant': self.user1.pk}
        self.assertDictEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_participant_retrieve_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.get(f'/api/participants/{participant.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_partial_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.patch(f'/api/participants/{participant.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 200)
        participant.refresh_from_db()
        self.assertEqual('NEW_TITLE', participant.title)
        self.client.credentials()
        project.delete()

    def test_api_participant_partial_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.patch(f'/api/participants/{participant.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_partial_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.patch(f'/api/participants/{participant.id}/', data={'title': 'NEW_TITLE'}, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_participant_update_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        data = self.participant_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/participants/{participant.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 200)
        participant.refresh_from_db()
        self.assertEqual('UPDATE_TITLE', participant.title)
        self.assertEqual('UPDATE_DESC', participant.description)
        self.client.credentials()
        project.delete()

    def test_api_participant_update_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        data = self.participant_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/participants/{participant.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_update_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        data = self.participant_info.copy()
        data['project'] = project.pk
        response = self.client.put(f'/api/participants/{participant.id}/', data=data, format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_participant_submit_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        response = self.client.post(f'/api/participants/{participant.id}/submit/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, participant.applications.count())
        self.client.credentials()
        project.delete()

    def test_api_participant_submit_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        response = self.client.post(f'/api/participants/{participant.id}/submit/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_clear_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.post(f'/api/participants/{participant.id}/clear/', format='json')
        self.assertEqual(response.status_code, 204)
        participant.refresh_from_db()
        self.assertTrue(self.user1.notifications.filter(
            text=f'Вы были удалены с роли {participant.title} в проекте {project.title}').exists())
        self.assertIsNone(participant.participant)
        self.client.credentials()
        project.delete()

    def test_api_participant_clear_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user1)
        response = self.client.post(f'/api/participants/{participant.id}/clear/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_clear_not_creator_or_participant(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project,
                                                 participant=self.user2)
        response = self.client.post(f'/api/participants/{participant.id}/clear/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_participant_applications_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.get(f'/api/participants/{participant.id}/applications/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = [{'id': application.id, 'vacancy': {'id': participant.id, 'project': project.id, 'title': 'Part1',
                                                       'description': 'PartDesc1',
                                                       'participant': None},
                     'applicant': {'id': self.user1.id, 'full_name': '', 'description': '', 'email': 'vlad@vk.ru',
                                   'phone': None,
                                   'cv': None, 'interests': [{'id': self.interest1.id, 'title': 'Math'}],
                                   'avatar': None}}]
        self.assertEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_participant_applications_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        response = self.client.get(f'/api/participants/{participant.id}/applications/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_participant_applications_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        response = self.client.get(f'/api/participants/{participant.id}/applications/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class ApplicationApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.interest1 = Interest.objects.create(title='Math')
        cls.interest2 = Interest.objects.create(title='Physics')
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user1.interests.add(cls.interest1)
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.project_info = {
            'title': 'Title1', 'description': 'Desc1',
            'application_deadline': datetime.date.today() + datetime.timedelta(days=1),
            'completion_deadline': datetime.date.today() + datetime.timedelta(days=3),
            'creator': cls.user1
        }
        cls.participant_info = {
            'title': 'UPDATE_TITLE', 'description': 'UPDATE_DESC'
        }
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_applications_mine_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.get(f'/api/applications/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = [{'id': application.id, 'vacancy': {'id': participant.id, 'project': project.id, 'title': 'Part1',
                                                       'description': 'PartDesc1',
                                                       'participant': None},
                     'applicant': {'id': self.user1.id, 'full_name': '', 'description': '', 'email': 'vlad@vk.ru',
                                   'phone': None,
                                   'cv': None, 'interests': [{'id': self.interest1.id, 'title': 'Math'}],
                                   'avatar': None}}]
        self.assertEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_applications_mine_unauthorized(self):
        response = self.client.get(f'/api/applications/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_application_retrieve_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.get(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        expected = {'id': application.id, 'vacancy': {'id': participant.id, 'project': project.id, 'title': 'Part1',
                                                      'description': 'PartDesc1',
                                                      'participant': None},
                    'applicant': {'id': self.user1.id, 'full_name': '', 'description': '', 'email': 'vlad@vk.ru',
                                  'phone': None,
                                  'cv': None, 'interests': [{'id': self.interest1.id, 'title': 'Math'}],
                                  'avatar': None}}
        self.assertDictEqual(expected, response.json())
        self.client.credentials()
        project.delete()

    def test_api_application_retrieve_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.get(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_application_retrieve_not_creator_or_applicant(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        response = self.client.get(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_application_destroy_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        response = self.client.delete(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 204)
        self.assertTrue(self.user2.notifications.filter(
            text=f'Ваша заявка на роль {participant.title} в проекте {project.title} отклонена').exists())
        self.assertEqual(0, participant.applications.count())
        self.client.credentials()
        project.delete()

    def test_api_application_destroy_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.delete(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_application_destroy_not_creator_or_applicant(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        response = self.client.delete(f'/api/applications/{application.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    def test_api_application_accept_authorized(self):
        self.set_credentials(self.user1)
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.post(f'/api/applications/{application.id}/accept/', format='json')
        self.assertEqual(response.status_code, 204)
        participant.refresh_from_db()
        self.assertEqual(self.user2, participant.participant)
        self.assertTrue(self.user2.notifications.filter(
            text=f'Ваша заявка на роль {participant.title} в проекте {project.title} одобрена').exists())
        self.assertTrue(self.user1.notifications.filter(
            text=f'Ваша заявка на роль {participant.title} в проекте {project.title} отклонена').exists())
        self.assertEqual(0, participant.applications.count())
        self.client.credentials()
        project.delete()

    def test_api_application_accept_unauthorized(self):
        project = Project.objects.create(**self.project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user1)
        response = self.client.post(f'/api/applications/{application.id}/accept/', format='json')
        self.assertEqual(response.status_code, 401)
        project.delete()

    def test_api_application_accept_not_creator(self):
        self.set_credentials(self.user1)
        new_project_info = self.project_info.copy()
        new_project_info['creator'] = self.user2
        project = Project.objects.create(**new_project_info)
        participant = Participant.objects.create(title='Part1', description='PartDesc1', project=project)
        application = Application.objects.create(vacancy=participant, applicant=self.user2)
        response = self.client.post(f'/api/applications/{application.id}/accept/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        project.delete()

    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()


class NotificationApiTestCase(TestCase):
    client_class = APIClient

    @classmethod
    def setUpClass(cls):
        cls.user1 = User.objects.create_user(email='vlad@vk.ru')
        cls.user2 = User.objects.create_user(email='ivan@bk.ru')
        cls.mock_authenticate = patch('account.authentication.EmailAuthBackend.authenticate').start()
        cls.mock_authenticate.return_value = cls.user1

    def set_credentials(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_HSE_AUTH=token.key)

    def test_api_notifications_mine_authorized(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.get(f'/api/notifications/mine/', format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()))
        result = response.json()[0]
        self.assertEqual(notification.id, result['id'])
        self.assertEqual(notification.text, result['text'])
        self.assertEqual(notification.unread, result['unread'])
        self.client.credentials()
        notification.delete()

    def test_api_notifications_mine_unauthorized(self):
        response = self.client.get(f'/api/notifications/mine/', format='json')
        self.assertEqual(response.status_code, 401)

    def test_api_notification_retrieve_authorized(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.get(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(notification.id, result['id'])
        self.assertEqual(notification.text, result['text'])
        self.assertEqual(notification.unread, result['unread'])
        self.client.credentials()
        notification.delete()

    def test_api_notification_retrieve_unauthorized(self):
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.get(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        notification.delete()

    def test_api_notification_retrieve_not_user(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user2, text='Notif')
        response = self.client.get(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        notification.delete()

    def test_api_notification_destroy_authorized(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user1, text='Notif')
        self.assertEqual(1, self.user1.notifications.count())
        response = self.client.delete(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, self.user1.notifications.count())
        self.client.credentials()

    def test_api_notification_destroy_unauthorized(self):
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.delete(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 401)
        notification.delete()

    def test_api_notification_destroy_not_user(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user2, text='Notif')
        response = self.client.delete(f'/api/notifications/{notification.id}/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        notification.delete()

    def test_api_notifications_clear_authorized(self):
        self.set_credentials(self.user1)
        notification1 = Notification.objects.create(user=self.user1, text='Notif')
        notification2 = Notification.objects.create(user=self.user1, text='Notif2')
        self.assertEqual(2, self.user1.notifications.count())
        response = self.client.post(f'/api/notifications/clear/', format='json')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(0, self.user1.notifications.count())
        self.client.credentials()

    def test_api_notifications_clear_unauthorized(self):
        notification1 = Notification.objects.create(user=self.user1, text='Notif')
        notification2 = Notification.objects.create(user=self.user1, text='Notif2')
        response = self.client.post(f'/api/notifications/clear/', format='json')
        self.assertEqual(response.status_code, 401)
        notification1.delete()
        notification2.delete()

    def test_api_notifications_read_all_authorized(self):
        self.set_credentials(self.user1)
        notification1 = Notification.objects.create(user=self.user1, text='Notif')
        notification2 = Notification.objects.create(user=self.user1, text='Notif2')
        response = self.client.post(f'/api/notifications/read_all/', format='json')
        self.assertEqual(response.status_code, 204)
        notification1.refresh_from_db()
        self.assertEqual(False, notification1.unread)
        notification2.refresh_from_db()
        self.assertEqual(False, notification2.unread)
        self.client.credentials()
        notification1.delete()
        notification2.delete()

    def test_api_notifications_read_all_unauthorized(self):
        notification1 = Notification.objects.create(user=self.user1, text='Notif')
        notification2 = Notification.objects.create(user=self.user1, text='Notif2')
        response = self.client.post(f'/api/notifications/read_all/', format='json')
        self.assertEqual(response.status_code, 401)
        notification1.delete()
        notification2.delete()

    def test_api_notifications_unread_all_authorized(self):
        self.set_credentials(self.user1)
        notification1 = Notification.objects.create(user=self.user1, text='Notif', unread=False)
        notification2 = Notification.objects.create(user=self.user1, text='Notif2', unread=False)
        response = self.client.post(f'/api/notifications/unread_all/', format='json')
        self.assertEqual(response.status_code, 204)
        notification1.refresh_from_db()
        self.assertEqual(True, notification1.unread)
        notification2.refresh_from_db()
        self.assertEqual(True, notification2.unread)
        self.client.credentials()
        notification1.delete()
        notification2.delete()

    def test_api_notifications_unread_all_unauthorized(self):
        notification1 = Notification.objects.create(user=self.user1, text='Notif')
        notification2 = Notification.objects.create(user=self.user1, text='Notif2')
        response = self.client.post(f'/api/notifications/unread_all/', format='json')
        self.assertEqual(response.status_code, 401)
        notification1.delete()
        notification2.delete()

    def test_api_notification_read_authorized(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.post(f'/api/notifications/{notification.id}/read/', format='json')
        self.assertEqual(response.status_code, 204)
        notification.refresh_from_db()
        self.assertEqual(False, notification.unread)
        self.client.credentials()
        notification.delete()

    def test_api_notification_read_unauthorized(self):
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.post(f'/api/notifications/{notification.id}/read/', format='json')
        self.assertEqual(response.status_code, 401)
        notification.delete()

    def test_api_notification_read_not_user(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user2, text='Notif')
        response = self.client.post(f'/api/notifications/{notification.id}/read/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        notification.delete()

    def test_api_notification_unread_authorized(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user1, text='Notif', unread=False)
        response = self.client.post(f'/api/notifications/{notification.id}/unread/', format='json')
        self.assertEqual(response.status_code, 204)
        notification.refresh_from_db()
        self.assertEqual(True, notification.unread)
        self.client.credentials()
        notification.delete()

    def test_api_notification_unread_unauthorized(self):
        notification = Notification.objects.create(user=self.user1, text='Notif')
        response = self.client.post(f'/api/notifications/{notification.id}/unread/', format='json')
        self.assertEqual(response.status_code, 401)
        notification.delete()

    def test_api_notification_unread_not_user(self):
        self.set_credentials(self.user1)
        notification = Notification.objects.create(user=self.user2, text='Notif')
        response = self.client.post(f'/api/notifications/{notification.id}/unread/', format='json')
        self.assertEqual(response.status_code, 403)
        self.client.credentials()
        notification.delete()

    @classmethod
    def tearDownClass(cls):
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
