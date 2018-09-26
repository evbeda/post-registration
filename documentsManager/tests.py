from django.core.urlresolvers import resolve
from django.contrib.auth import get_user_model
from django.test import TestCase
from social_django.models import UserSocialAuth
from unittest.mock import patch


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='kaizen',
            password='awesome',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        # self.user.set_password('hello')
        # self.user.save()
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='eventbrite',
        )
        login = self.client.login(username='kaizen', password='awesome')
        return login


class DocFormTest(TestBase):

    def setUp(self):
        super(DocFormTest, self).setUp()

    def test_doc_from_exist(self):
        view = resolve('/docs_form/')
        self.assertEqual(view.view_name, 'doc_form')

    def test_home_url_resolves_home_view(self):
        view = resolve('/')
        self.assertEqual(view.view_name, 'index')

    def test_events_exist(self):
        view = resolve('/events/')
        self.assertEqual(view.view_name, 'events')

    def test_redirect(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    def test_events_redirect(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    def test_doc_redirect(self):
        response = self.client.get('/docs_form/?id=49213916148')
        self.assertEqual(response.status_code, 200)

    def test_homepage_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

