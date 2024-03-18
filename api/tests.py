from unittest.mock import patch

from django.test import TestCase
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from account.models import User, Interest
from projects.models import Project, Participant


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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

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
        self.assertEqual(['id', 'full_name', 'description', 'email', 'phone', 'cv', 'interests'], list(data.keys()))
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
        self.assertEqual(['id', 'full_name', 'description', 'email', 'phone', 'cv', 'interests'], list(data.keys()))
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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

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
            'application_deadline': '2024-04-05',
            'completion_deadline': '2024-04-07',
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
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)

    def test_api_project_create_authorized(self):
        self.set_credentials(self.user1)
        data = {'title': 'Title1', 'description': 'Desc1', 'application_deadline': '2024-04-06',
                'completion_deadline': '2024-04-09', 'checkpoints': [],
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


    @classmethod
    def tearDownClass(cls):
        cls.interest1.delete()
        cls.interest2.delete()
        cls.user1.delete()
        cls.user2.delete()
        cls.mock_authenticate.stop()
