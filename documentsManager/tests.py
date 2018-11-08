from datetime import datetime

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.core.urlresolvers import resolve, reverse
from django.db.utils import DataError
from django.template.loader import render_to_string
from django.test import Client, TestCase
from social_django.models import UserSocialAuth
from unittest.mock import patch

from documentsManager.apps import DocumentsmanagerConfig
from documentsManager.forms import (
    EventForm,
    TextDocForm,
    SignUpForm,
    EvaluatorForm,
    validate_text_submissions,
    validate_files_submissions,
    SubmissionForm,
)
from documentsManager.models import (
    Event,
    TextDoc,
    FileType,
    FileDoc,
    Evaluator,
    User,
    EvaluatorEvent,
    FileSubmission,
    Review,
    Submission,
)
from documentsManager.views import (
    add_event,
    filter_managed_event,
    filter_no_managed_event,
    get_auth_token,
)
from post_registration.settings import get_env_variable


MOCK_EVENTS_API = {
    'name': {
        'text': 'EventoCualquiera',
        'html': 'EventoCualquiera'
    },
    'description': {
        'text': None,
        'html': None
    },
    'id': '50607739110',
    'url': 'https://www.eventbrite.com.ar/e/eventocualquiera-tickets-50607739110',
    'start': {
        'timezone': 'America/Caracas',
        'local': '2018-11-03T19:00:00',
        'utc': '2018-11-03T23:00:00Z'
    },
    'end': {
        'timezone': 'America/Caracas',
        'local': '2018-11-03T22:00:00',
        'utc': '2018-11-04T02:00:00Z'
    },
    'organization_id': '226660633266',
    'created': '2018-09-24T17:32:37Z',
    'changed': '2018-09-26T17:07:55Z',
    'capacity': 10,
    'capacity_is_custom': False,
    'status': 'live',
    'currency': 'ARS',
    'listed': False,
    'shareable': True,
    'invite_only': False,
    'online_event': False,
    'show_remaining': False,
    'tx_time_limit': 480,
    'hide_start_date': False,
    'hide_end_date': False,
    'locale': 'es_AR',
    'is_locked': False,
    'privacy_setting': 'unlocked',
    'is_series': False,
    'is_series_parent': False,
    'is_reserved_seating': False,
    'show_pick_a_seat': False,
    'show_seatmap_thumbnail': False,
    'show_colors_in_seatmap_thumbnail': False,
    'source': 'create_2.0',
    'is_free': True,
    'version': '3.0.0',
    'logo_id': '50285339',
    'organizer_id': '17688321548',
    'venue_id': None,
    'category_id': None,
    'subcategory_id': None,
    'format_id': None,
    'resource_uri': 'https://www.eventbriteapi.com/v3/events/50607739110/',
    'is_externally_ticketed': False,
    'logo': {
        'crop_mask': {
            'top_left': {
                'x': 0,
                'y': 43
            },
            'width': 524,
            'height': 262
        },
        'original': {
            'url': 'https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2F'
                   'images%2F50285339%2F226660633266%2F1%2Foriginal.jpg?'
                   'auto=compress&s=76bcc2208a37ed4a6cf52ec9d204fe1c',
            'width': 525,
            'height': 350
        },
        'id': '50285339',
        'url': 'https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2Fimages'
               '%2F50285339%2F226660633266%2F1%2Foriginal.jpg?h=200&w=450&'
               'auto=compress&rect=0%2C43%2C524%2C262&s=393615fb1d44a82eb37a2cb2fafa9ac7',
        'aspect_ratio': '2',
        'edge_color': '#6b7384',
        'edge_color_set': True
    }
}

MOCK_EVENTS_API_2 = {
    'name': {
        'text': 'EventoCualquiera2',
        'html': 'EventoCualquiera2'
    },
    'description': {
        'text': None,
        'html': None
    },
    'id': '50607739120',
    'url': 'https://www.eventbrite.com.ar/e/eventocualquiera-tickets-50607739110',
    'start': {
        'timezone': 'America/Caracas',
        'local': '2018-11-03T19:00:00',
        'utc': '2018-11-03T23:00:00Z'
    },
    'end': {
        'timezone': 'America/Caracas',
        'local': '2018-11-03T22:00:00',
        'utc': '2018-11-04T02:00:00Z'
    },
    'organization_id': '226660633266',
    'created': '2018-09-24T17:32:37Z',
    'changed': '2018-09-26T17:07:55Z',
    'capacity': 10,
    'capacity_is_custom': False,
    'status': 'live',
    'currency': 'ARS',
    'listed': False,
    'shareable': True,
    'invite_only': False,
    'online_event': False,
    'show_remaining': False,
    'tx_time_limit': 480,
    'hide_start_date': False,
    'hide_end_date': False,
    'locale': 'es_AR',
    'is_locked': False,
    'privacy_setting': 'unlocked',
    'is_series': False,
    'is_series_parent': False,
    'is_reserved_seating': False,
    'show_pick_a_seat': False,
    'show_seatmap_thumbnail': False,
    'show_colors_in_seatmap_thumbnail': False,
    'source': 'create_2.0',
    'is_free': True,
    'version': '3.0.0',
    'logo_id': '50285339',
    'organizer_id': '17688321548',
    'venue_id': None,
    'category_id': None,
    'subcategory_id': None,
    'format_id': None,
    'resource_uri': 'https://www.eventbriteapi.com/v3/events/50607739110/',
    'is_externally_ticketed': False,
    'logo': {
        'crop_mask': {
            'top_left': {
                'x': 0,
                'y': 43
            },
            'width': 524,
            'height': 262
        },
        'original': {
            'url': 'https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2F'
                   'images%2F50285339%2F226660633266%2F1%2Foriginal.jpg?'
                   'auto=compress&s=76bcc2208a37ed4a6cf52ec9d204fe1c',
            'width': 525,
            'height': 350
        },
        'id': '50285339',
        'url': 'https://img.evbuc.com/https%3A%2F%2Fcdn.evbuc.com%2Fimages'
               '%2F50285339%2F226660633266%2F1%2Foriginal.jpg?h=200&w=450&'
               'auto=compress&rect=0%2C43%2C524%2C262&s=393615fb1d44a82eb37a2cb2fafa9ac7',
        'aspect_ratio': '2',
        'edge_color': '#6b7384',
        'edge_color_set': True
    }
}


class TestBase(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser(
            email='kaizen@email.com',
            password='awesome1234',
        )
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='eventbrite',
            extra_data={
                "auth_time": 1538166097,
                "access_token": "hsadfkjashdbfkjahsdbf",
                "token_type": "bearer"
            },
        )
        login = self.client.login(
            username='kaizen@email.com', password='awesome1234')
        return login

    def create_event(self, eb_event_id=1):
        return Event.objects.create(eb_event_id=eb_event_id, organizer=self.user)

    def create_evaluator(self, name='John', email='john@email.com'):
        return Evaluator.objects.create(name=name, email=email)


class ViewTest(TestBase):

    def setUp(self):
        super(ViewTest, self).setUp()

    def test_doc_from_exist(self):
        view = resolve('/doc_form/12/')
        self.assertEqual(view.view_name, 'doc_form')

    def test_docs_from_exist(self):
        view = resolve('/event/13/docs/')
        self.assertEqual(view.view_name, 'docs')

    def test_home_url_resolves_home_view(self):
        view = resolve('/')
        self.assertEqual(view.view_name, 'home')

    def test_events_exist(self):
        view = resolve('/events/')
        self.assertEqual(view.view_name, 'events')

    def test_redirect(self):
        response = self.client.get('/accounts/login/')
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_access_submission_dashboard(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        response = self.client.get('/event/{}/submissions/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_docs_redirect(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        response = self.client.get('/event/{}/docs/'.format(new_event.id))
        self.assertEqual(response.status_code, 200)

    def test_events_redirect(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_doc_form_redirect(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        response = self.client.get('/doc_form/{}/'.format(new_event.id))
        self.assertEqual(response.status_code, 200)

    def test_homepage_redirect(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_filter(self):
        api_events = [{'eb_id': '1'}, {'eb_id': '2'}, {'eb_id': '3'}]
        model_events = [['1', '1'], ['3', '3']]
        result = filter_managed_event(api_events, model_events)
        self.assertEqual(len(result), 2)

    def test_events_filter(self):
        api_events = [{'eb_id': '1'}, {'eb_id': '2'}, {'eb_id': '3'}]
        model_events = ['1', '3']
        result = filter_no_managed_event(api_events, model_events)
        self.assertEqual(len(result), 1)

    @patch('documentsManager.views.Eventbrite.get')
    def test_create_and_save_event(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        response = self.client.get('/events/50285339/')
        event = Event.objects.get(eb_event_id=50285339)
        expect = '/event/{}/docs/'.format(event.id)
        self.assertEqual(response.url, expect)

    def test_modify_event_dates(self):
        EVB_ID = 1234
        new_event = add_event(EVB_ID, '2018-03-03', organizer=self.user)
        new_event.init_submission = datetime.strptime(
            '2018-01-01', '%Y-%m-%d').date()
        new_event.save()
        r = {
            'init_submission': '2018-02-01',
            'end_submission': '2018-02-25',
        }
        response = self.client.post(
            '/event/{}/docs/'.format(new_event.id),
            r,
        )
        result = Event.objects.get(id=new_event.id)
        expected = datetime.strptime('2018-02-01', '%Y-%m-%d').date()
        self.assertEqual(result.init_submission, expected)
        self.assertEqual(response.url, '/event/{}/docs/'.format(new_event.id))

    @patch('documentsManager.views.Eventbrite.get')
    def test_response_with_landing_page(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        event = Event.objects.create(eb_event_id=321, organizer=self.user)
        event.end_submission = '2018-02-25'
        response = self.client.get('/landing/{}/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    def test_response_with_success(self):
        event = Event.objects.create(eb_event_id=321, organizer=self.user)
        response = self.client.get('/landing/{}/success/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_response_with_landing_page_with_text_doc(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        event = Event.objects.create(eb_event_id=321, organizer=self.user)
        TextDoc.objects.create(event=event)
        FileDoc.objects.create(event=event)
        response = self.client.get('/landing/{}/'.format(event.id))
        self.assertTrue('text_docs' in response.context)
        self.assertTrue('file_docs' in response.context)

    @patch('documentsManager.views.Eventbrite.get')
    def test_submission_view_review(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        event = Event.objects.create(
            eb_event_id=50607739110, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        file = File(open('runtime.txt', 'rb'))
        file_submission_1 = FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=event,
        )
        FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=event,
        )
        evaluator = Evaluator.objects.create(email='eval@eval.com')
        EvaluatorEvent.objects.create(
            event=event,
            evaluator=evaluator,
            status='accepted',
        )
        User.objects.create_superuser(
            email='eval@eval.com',
            password='john1234',
        )
        submission = Submission.objects.get(
            id=file_submission_1.submission_ptr_id)
        Review.objects.create(
            aproved=True, evaluator=evaluator, submission=submission)
        self.client.login(email='eval@eval.com', password='john1234')
        response = self.client.get('/accounts/login/', follow=True)
        response2 = self.client.get(
            response.context_data['next'], follow=True, **{'HTTP_REFERER': 'accounts/login'})
        self.assertEqual(
            len(response2.context['submissions_without_review']), 1)
        self.assertEqual(len(response2.context['submissions_with_review']), 1)


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
        self.user = User.objects.create_superuser(
            email='mike@email.com',
            password='genius1234',
        )
        self.auth = UserSocialAuth.objects.create(
            user=self.user,
            provider='kaizenbrite',
        )
        with self.assertRaises(Exception) as context:
            get_auth_token(self.user)
        self.assertTrue(
            'UserSocialAuth does not exists!' in str(context.exception))


class ModelsTest(TestBase):
    def test_model_text_exist(self):
        new_event = Event.objects.create(eb_event_id=3, organizer=self.user)
        text_doc = TextDoc.objects.create(event=new_event)
        self.assertEqual(text_doc.name, '')
        self.assertEqual(text_doc.measure, 'Words')
        self.assertEqual(text_doc.max, 500)
        self.assertEqual(text_doc.min, 10)
        self.assertEqual(text_doc.is_optional, False)

    def test_model_file_type(self):
        new_event = FileType.objects.create(name='PDF')
        result = str(new_event)
        self.assertEqual(result, 'PDF ()')

    def test_model_text_error_max_word(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.max = 'asd'
        result = isinstance(text_doc.max, int)
        self.assertFalse(result)

    def test_model_text_max_word(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.max = 237
        result = isinstance(text_doc.max, int)
        self.assertTrue(result)

    def test_model_text_error_max_word_2(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.min = 'asd'
        result = isinstance(text_doc.min, int)
        self.assertFalse(result)

    def test_model_text_max_word_2(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.min = 4560
        result = isinstance(text_doc.min, int)
        self.assertTrue(result)

    def test_model_file_quantity_only_recieve_ints(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.quantity = 'asd'
        with self.assertRaises(ValueError):
            file_doc.save()

    def test_model_file_quantity_is_int(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.quantity = 123
        result = isinstance(file_doc.quantity, int)
        self.assertTrue(result)

    def test_model_file_name_submission_invalid(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        with self.assertRaises(DataError) as data_error:
            FileDoc.objects.create(
                event=new_event,
                name='asd' * 50,
            )
        self.assertEqual(data_error.exception.args,
                         ('value too long for type character varying(100)\n',))

    def test_model_file_name_submission_valid(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.name = ('Documento')
        self.assertEqual(file_doc.name, 'Documento')

    def test_model_text_doc_name_submission_invalid(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        with self.assertRaises(DataError) as data_error:
            TextDoc.objects.create(
                event=new_event,
                name='asd' * 50,
            )
        self.assertEqual(data_error.exception.args,
                         ('value too long for type character varying(100)\n',))

    def test_model_text_doc_name_submission_valid(self):
        new_event = Event.objects.create(eb_event_id=1, organizer=self.user)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.name = ('Foto')
        self.assertEqual(file_doc.name, 'Foto')


class SignUpView(TestBase):
    def test_signup_view_name(self):
        view = resolve(reverse('signup'))
        self.assertEqual(view.url_name, 'signup')


class EvaluatorTest(TestBase):

    def setUp(self):
        super(EvaluatorTest, self).setUp()

    def test_create_evaluator(self):
        evaluator = self.create_evaluator()
        self.assertTrue(isinstance(evaluator, Evaluator))

    def test_evaluator_string_representation(self):
        evaluator = self.create_evaluator()
        self.assertEquals(str(evaluator), evaluator.name)

    def test_evaluator_verbose_name_plural(self):
        self.assertEqual(
            str(Evaluator._meta.verbose_name_plural), "evaluators")

    @patch('documentsManager.views.Eventbrite.get')
    def test_login_with_Eval_1_accepted(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        new_event = Event.objects.create(
            eb_event_id=50607739110, organizer=self.user)
        evaluator = Evaluator.objects.create(email='john@email.com')
        EvaluatorEvent.objects.create(
            event=new_event,
            evaluator=evaluator,
            status='accepted',
        )
        EvaluatorEvent.objects.create(
            event=new_event,
            evaluator=evaluator,
            status='pending',
        )
        User.objects.create_superuser(
            email='john@email.com',
            password='john1234',
        )
        self.client.login(email='john@email.com', password='john1234')
        response = self.client.get('/accounts/login/', follow=True)
        response2 = self.client.get(
            response.context_data['next'], follow=True, **{'HTTP_REFERER': 'accounts/login'})
        self.assertEquals(
            response2.wsgi_request.path,
            '/event/{}/submissions/'.format(new_event.id),
        )

    @patch('documentsManager.views.Eventbrite.get')
    @patch('documentsManager.views.Eventbrite.get')
    def test_login_with_Eval_2_accepted(self, mock_eventbrite_get, mock_eventbrite_get_2):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        mock_eventbrite_get_2.return_value = MOCK_EVENTS_API_2
        new_event_1 = Event.objects.create(
            eb_event_id=50607739110, organizer=self.user)
        new_event_2 = Event.objects.create(
            eb_event_id=50607739120, organizer=self.user)
        evaluator_1 = Evaluator.objects.create(email='john@email.com')
        EvaluatorEvent.objects.create(
            event=new_event_1,
            evaluator=evaluator_1,
            status='accepted',
        )
        EvaluatorEvent.objects.create(
            event=new_event_2,
            evaluator=evaluator_1,
            status='accepted',
        )
        User.objects.create_superuser(
            email='john@email.com',
            password='john1234',
        )
        self.client.login(email='john@email.com', password='john1234')
        response = self.client.get('/accounts/login/', follow=True)
        response2 = self.client.get(
            response.context_data['next'], follow=True, **{'HTTP_REFERER': 'accounts/login'})
        self.assertEquals(response2.wsgi_request.path, '/')


@patch('documentsManager.views.get_one_event_api')
class EvaluatorListTest(TestBase):
    def test_evaluator_list_view_name(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        view = resolve(reverse('evaluators', kwargs={'event_id': event.id}))
        self.assertEqual(view.url_name, 'evaluators')

    def test_evaluator_list_response_status(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        self.create_evaluator()
        response = self.client.get(
            reverse('evaluators', kwargs={'event_id': event.id}))
        self.assertEquals(response.status_code, 200)

    def test_evaluator_uses_correct_template(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        response = self.client.get(
            reverse('evaluators', kwargs={'event_id': event.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'evaluators_grid.html')

    def test_evaluator_list_response_content(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        evaluator = self.create_evaluator()
        EvaluatorEvent.objects.create(
            event=event,
            evaluator=evaluator,
        )
        response = self.client.get(
            reverse(
                'evaluators',
                kwargs={'event_id': event.id}
            )
        )
        self.assertContains(response, evaluator)


class EvaluatorCreateTest(TestBase):

    def test_evaluator_create_view_name(self):
        event = self.create_event()
        view = resolve(reverse('evaluator_create',
                               kwargs={'event_id': event.id}))
        self.assertEqual(view.url_name, 'evaluator_create')

    def test_evaluator_create_response_status(self):
        event = self.create_event()
        self.create_evaluator()
        response = self.client.get(
            reverse('evaluator_create', kwargs={'event_id': event.id}))
        self.assertEquals(response.status_code, 200)

    def test_evaluator_uses_correct_template(self):
        event = self.create_event()
        response = self.client.get(
            reverse('evaluator_create', kwargs={'event_id': event.id}))
        self.assertEquals(response.status_code, 200)
        self.assertTemplateUsed(response, 'evaluator_form.html')

    @patch('documentsManager.forms.render_to_string')
    @patch('documentsManager.views.get_one_event_api')
    def test_evaluator_success_url(self, mock_get_one_event_api, mock_render_to_string):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        mock_render_to_string.return_value = render_to_string('empty.html', {})
        event = self.create_event()
        data = {
            'name': 'John',
            'email': 'john@ejemplo.com',
        }
        response = self.client.post(
            reverse(
                'evaluator_create',
                kwargs={
                    'event_id': event.id,
                }
            ),
            data
        )
        self.assertRedirects(response, reverse(
            'evaluators', kwargs={'event_id': event.id}))


@patch('documentsManager.views.get_one_event_api')
class EvaluatorUpdateTest(TestBase):

    def test_evaluator_redirect_on_update(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        evaluator = self.create_evaluator()
        event = self.create_event()
        data = {
            'name': 'Jack',
            'email': 'test@mail.com',
        }
        response = self.client.post(
            reverse('evaluator_update', kwargs={
                'event_id': event.id, 'pk': evaluator.id}),
            data
        )
        self.assertRedirects(response, reverse(
            'evaluators', kwargs={'event_id': event.id}))

    def test_evaluator_update_success(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = MOCK_EVENTS_API
        evaluator = self.create_evaluator()
        evaluator.save()
        event = self.create_event()
        data = {
            'name': 'Jack',
            'email': 'test@mail.com',
        }
        response = self.client.post(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': event.id,
                    'pk': evaluator.id,
                }
            ),
            data
        )
        self.assertEqual(response.status_code, 302)
        evaluator.refresh_from_db()
        self.assertEqual(evaluator.name, 'Jack')
        self.assertEqual(evaluator.email, 'test@mail.com')

    def test_evaluator_update_context(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = MOCK_EVENTS_API
        evaluator = self.create_evaluator()
        evaluator.save()
        event = self.create_event()
        data = {
            'name': 'Jack',
            'email': 'test@mail.com',
        }
        response = self.client.get(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': event.id,
                    'pk': evaluator.id,
                }
            )
        )
        self.assertContains(response, event.id)


@patch('documentsManager.views.get_one_event_api')
class EvaluatorDeleteTest(TestBase):

    def test_evaluator_success_redirect(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        evaluator = self.create_evaluator()
        response = self.client.post(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': event.id,
                    'pk': evaluator.id,
                }
            ),
        )
        self.assertRedirects(response, reverse(
            'evaluators',
            kwargs={'event_id': event.id}
        ))

    def test_cannot_evaluator_delete_twice(self, mock_get_one_event_api):
        event = self.create_event()
        evaluator = self.create_evaluator()
        self.client.post(
            reverse('evaluator_delete', kwargs={
                'event_id': event.id, 'pk': evaluator.id}),
        )
        response = self.client.post(
            reverse('evaluator_delete', kwargs={
                'event_id': event.id, 'pk': evaluator.id}),
        )
        self.assertEquals(response.status_code, 404)

    def test_evaluator_dissapear_from_db(self, mock_get_one_event_api):
        event = self.create_event()
        evaluator = self.create_evaluator()

        self.client.post(
            reverse('evaluator_delete', kwargs={
                'event_id': event.id, 'pk': evaluator.id}),
        )
        self.assertFalse(Evaluator.objects.filter(pk=evaluator.id).exists())

    def test_evaluator_delete_context(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        evaluator = self.create_evaluator()
        response = self.client.get(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': event.id,
                    'pk': evaluator.id,
                }
            ),
        )
        self.assertContains(response, event.id)


class EvaluatorFormTest(TestBase):
    def test_valid_form(self):
        e = self.create_evaluator(email='john@mail.com')
        data = {'name': e.name, 'email': e.email, }
        form = EvaluatorForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        e = Evaluator.objects.create(name='John', email='johnmail.com')
        data = {'name': e.name, 'email': e.email, }
        form = EvaluatorForm(data=data)
        self.assertFalse(form.is_valid())


class EvaluatorEventTest(TestBase):
    def test_create_a_model(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        evaluator = Evaluator.objects.create(name='Leo', email='leo@leo.com')
        evaluator_event = EvaluatorEvent.objects.create(
            event=event,
            evaluator=evaluator
        )
        self.assertTrue(isinstance(evaluator_event, EvaluatorEvent))

    def test_evaluator_event_initial_status(self):
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator_event = EvaluatorEvent.objects.create(
            event=event, evaluator=evaluator
        )
        self.assertEqual(evaluator_event.status, 'pending')


class AcceptInvitationViewTest(TestBase):

    @patch('documentsManager.views.render_to_string')
    def test_accept_invitation_state(self, mock_render_to_string):
        mock_render_to_string.return_value = render_to_string('empty.html', {})
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator_event = EvaluatorEvent.objects.create(
            event=event, evaluator=evaluator)
        response = self.client.get(
            reverse(
                'accept-invitation',
                kwargs={
                    'invitation_code': evaluator_event.invitation_code
                }
            )
        )
        evaluator_event.refresh_from_db()
        self.assertEqual(evaluator_event.status, 'accepted')


class DeclineInvitationViewTest(TestBase):
    def test_decline_invitation_state(self):
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator_event = EvaluatorEvent.objects.create(
            event=event, evaluator=evaluator)
        response = self.client.get(
            reverse(
                'decline-invitation',
                kwargs={
                    'invitation_code': evaluator_event.invitation_code
                }
            )
        )
        evaluator_event.refresh_from_db()
        self.assertEqual(evaluator_event.status, 'rejected')


class FormsTest(TestBase):

    def test_is_valid_EventForm(self):
        form = EventForm()
        result = form.is_valid()
        self.assertFalse(result)

    def test_is_not_valid_EventForm(self):
        init = datetime.strptime('2018-02-27', '%Y-%m-%d').date()
        end = datetime.strptime('2018-02-25', '%Y-%m-%d').date()
        form2 = EventForm({
            'init_submission': init,
            'end_submission': end,
        })
        result = form2.is_valid()
        self.assertFalse(result)

    def test_text_doc_form_is_invalid(self):
        form = TextDocForm({
            'name': 'CV',
            'is_optional': 'on',
            'measure': 'Words',
            'min': '400',
            'max': '300',
        })
        self.assertFalse(form.is_valid())

    def test_text_doc_form_is_empty(self):
        form = TextDocForm()
        result = form.is_valid()
        self.assertFalse(result)

    def test_text_doc_form_is_valid(self):
        form = TextDocForm({
            'name': 'CV',
            'is_optional': 'on',
            'measure': 'Words',
            'min': '400',
            'max': '500',
        })
        self.assertTrue(form.is_valid)

    def test_SignUp_Form(self):
        form = SignUpForm({
            'password1': 'password27',
            'password2': 'password27',
            'email': 'juan@ejemplo.com',
        })
        form.save()
        user = User.objects.get(email='juan@ejemplo.com')
        self.assertEqual(user.email, 'juan@ejemplo.com')

    def test_validate_text_submissions(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        text_doc = TextDoc.objects.create(event=event)
        key = '{}_text'.format(text_doc.id)
        text_fields = {
            key: 'a a a a a a a a a a'
        }
        result = validate_text_submissions(text_fields)
        expected = True
        self.assertEqual(result, expected)

    def test_validate_files_submissions(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        key = '{}_file'.format(file_doc.id)
        values = {
            key: ''
        }
        result = validate_files_submissions(values, event.id)
        self.assertEqual(result, True)

    def test_Submission_Form(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        text_doc = TextDoc.objects.create(event=event)
        key = '{}_text'.format(text_doc.id)
        form = SubmissionForm({
            key: 'a a a a a a a a a a'
        })
        self.assertEqual(form.is_valid(), True)

    def test_Submission_Form_with_files(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        key = '{}_file'.format(file_doc.id)
        form = SubmissionForm(
            files={
                key: ''
            },
            data={
                'event_id': event.id
            },
        )
        self.assertEqual(form.is_valid(), True)


class FileSubmissionTest(TestBase):
    def test_create_a_file_submission(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        file = File(open('runtime.txt', 'rb'))
        file_submission = FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=event,
        )
        result = isinstance(file_submission, FileSubmission)
        self.assertTrue(result)


@patch('documentsManager.views.create_order_webhook_from_view', return_value='')
class DashboardView(TestBase):
    def setUp(self):
        super(DashboardView, self).setUp()

    def test_home_status_code(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_home_charset(self, mock_create_order_webhook_from_view):
        response = self.client.get('/')
        self.assertEqual(response.charset, 'utf-8')

    def test_home_status_code_two(self, mock_create_order_webhook_from_view):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_home_resolve_home_not_args(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEquals(found.args, ())

    def test_home_url_name(self, mock_create_order_webhook_from_view):
        found = resolve('/')
        self.assertEqual(found.url_name, 'home')
