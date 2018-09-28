from django.apps import apps
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve
from django.test import TestCase
from social_django.models import UserSocialAuth

from documentsManager.apps import DocumentsmanagerConfig
from documentsManager.views import get_auth_token
from post_registration.settings import get_env_variable


class TestBase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='kaizen',
            password='awesome',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='eventbrite',
        )
        login = self.client.login(username='kaizen', password='awesome')
        return login


class TemplatesTest(TestBase):

    def setUp(self):
        super(TemplatesTest, self).setUp()

    def test_doc_from_exist(self):
        view = resolve('/doc_form/49213916148/')
        self.assertEqual(view.view_name, 'doc_form')

    def test_docs_from_exist(self):
        view = resolve('/docs/49213916148/')
        self.assertEqual(view.view_name, 'docs')

    def test_home_url_resolves_home_view(self):
        view = resolve('/')
        self.assertEqual(view.view_name, 'index')

    def test_events_exist(self):
        view = resolve('/events/')
        self.assertEqual(view.view_name, 'events')

    def test_redirect(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    # def test_docs_redirect(self):
    #     response = self.client.get('/docs/49213916148/')
    #     self.assertEqual(response.status_code, 200)

    def test_events_redirect(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    # def test_doc_form_redirect(self):
    #     response = self.client.get('/doc_form/49213916148/')
    #     self.assertEqual(response.status_code, 200)

    def test_homepage_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)


class DocumentsmanagerConfigTest(TestCase):
    def test_apps(self):
        self.assertEqual(DocumentsmanagerConfig.name, 'documentsManager')
        self.assertEqual(apps.get_app_config(
            'documentsManager').name, 'documentsManager')


class SettingsTest(TestCase):
    def test_env_exists(self):
        env_var = 'SOCIAL_AUTH_EVENTBRITE_KEY'
        result = get_env_variable(env_var)
        self.assertTrue(result)

    def test_env_not_exists(self):
        env_var = 'SOCIAL_AUTH_EVENTBRITE_KEY_FALSE'
        with self.assertRaises(ImproperlyConfigured) as context:
            get_env_variable(env_var)
        expected = 'Set the SOCIAL_AUTH_EVENTBRITE_KEY_FALSE environment variable'
        self.assertTrue(expected in str(context.exception))


class AuthTokenTest(TestCase):
    def test_error(self):
        self.user = get_user_model().objects.create_user(
            username='mike',
            password='genius',
            is_active=True,
            is_staff=True,
            is_superuser=True
        )
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='kaizenbrite',
        )
        with self.assertRaises(Exception) as context:
            get_auth_token(self.user)
        self.assertTrue(
            'UserSocialAuth does not exists!' in str(context.exception))
