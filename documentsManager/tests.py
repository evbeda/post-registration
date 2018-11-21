from datetime import datetime
from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.files import File
from django.core.urlresolvers import resolve, reverse
from django.db.utils import DataError
from django.template.loader import render_to_string
from django.test import Client
from django.test import TestCase
from social_django.models import UserSocialAuth

from documentsManager.apps import DocumentsmanagerConfig
from documentsManager.forms import (
    EventForm,
    TextDocForm,
    SignUpForm,
    EvaluatorForm,
    EvaluationDateForm,
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
    TextSubmission,
    Review,
    Submission,
    UserWebhook,
    Attendee,
    AttendeeCode,
)
from documentsManager.utils import (
    social_user_exists,
    get_data,
    webhook_available_to_process,
    get_social_user,
    send_email_to_attende,
    create_order_webhook_from_view,
    get_access_token_form_user_id,
    get_eventbrite_data,
    get_parsed_event,
    create_attendee_code,
    notify_attendee_from_attende_code,
    get_docs_from_event,
    send_success_submission_email,
    validate_files_submissions,
    validate_text_submissions,
    get_auth_token,
    filter_managed_event,
    filter_no_managed_event,
    add_event,
)
from post_registration import settings
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
    'venue_id': '123',
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
            username='kaizen@email.com',
            password='awesome1234'
        )
        return login

    def create_event(self, eb_event_id=1):
        return Event.objects.create(
            eb_event_id=eb_event_id,
            organizer=self.user)

    def create_evaluator(self, name='John', email='john@email.com'):
        return Evaluator.objects.create(name=name, email=email)


class ViewTest(TestBase):

    def setUp(self):
        super(ViewTest, self).setUp()
        self.event = Event.objects.create(eb_event_id=1, organizer=self.user)

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

    @patch('documentsManager.utils.Eventbrite.get')
    def test_access_submission_dashboard(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        event = self.event
        response = self.client.get('/event/{}/submissions/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.utils.Eventbrite.get')
    def test_docs_redirect(self, mock_eventbrite_get):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        new_event = self.event
        response = self.client.get('/event/{}/docs/'.format(new_event.id))
        self.assertEqual(response.status_code, 200)

    def test_events_redirect(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.utils.Eventbrite.get')
    def test_doc_form_redirect(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = self.event
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

    @patch('documentsManager.utils.Eventbrite.get')
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

    @patch('documentsManager.utils.Eventbrite.get')
    def test_response_with_landing_page(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        event = self.event
        event.end_submission = '2018-02-25'
        response = self.client.get('/landing/{}/preview/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    def test_response_with_success(self):
        event = self.event
        response = self.client.get('/landing/{}/success/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.utils.Eventbrite.get')
    def test_response_with_landing_page_with_text_doc(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        event = self.event
        TextDoc.objects.create(event=event)
        FileDoc.objects.create(event=event)
        response = self.client.get('/landing/{}/preview/'.format(event.id))
        self.assertTrue('text_docs' in response.context)
        self.assertTrue('file_docs' in response.context)

    @patch('documentsManager.utils.Eventbrite.get')
    def test_new_file_doc_submission(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = self.event
        data = {
            'name': 'prueba',
            'is_optional': 'on',
            'quantity': '2',
            'submit_file': 'Create',
        }
        response = self.client.post(
            reverse(
                'doc_form',
                kwargs={
                    'event_id': new_event.id,
                }
            ),
            data,
        )
        result = FileDoc.objects.filter(name='prueba').first()
        self.assertEqual(result.name, 'prueba')
        self.assertRedirects(response, reverse('docs', kwargs={'event_id': new_event.id}))

    @patch('documentsManager.utils.Eventbrite.get')
    def test_new_text_doc_submission(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = self.event
        data = {
            'name': 'CV',
            'is_optional': 'on',
            'measure': 'Words',
            'min': '100',
            'max': '300',
            'submit_text': 'Create',
        }
        response = self.client.post(
            reverse(
                'doc_form',
                kwargs={
                    'event_id': new_event.id,
                }
            ),
            data,
        )
        result = TextDoc.objects.filter(name='CV').first()
        self.assertEqual(result.name, 'CV')
        self.assertRedirects(response, reverse('docs', kwargs={'event_id': new_event.id}))

    @patch('documentsManager.utils.Eventbrite.get')
    def test_not_valid_text_doc_submission(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = self.event
        data = {
            'name': 'CV',
            'is_optional': 'on',
            'measure': 'Words',
            'min': '400',
            'max': '300',
            'submit_text': 'Create',
        }
        response = self.client.post(
            reverse(
                'doc_form',
                kwargs={
                    'event_id': new_event.id,
                }
            ),
            data,
        )
        self.assertFalse(response.context_data['forms']['file_doc'].is_valid())


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

    def test_user_raises_errors(self):
        self.assertRaises(
            ValueError,
            User.objects.create_superuser,
            email='prueba1@prueba.com',
            password='pass1234',
            is_staff='TRUE',
        )
        self.assertRaises(
            ValueError,
            User.objects.create_superuser,
            email='prueba2@prueba.com',
            password='pass1234',
            is_superuser='TRUE',
        )
        self.assertRaises(
            ValueError,
            User.objects.create_superuser,
            email='',
            password='pass1234',
        )


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

    @patch('documentsManager.utils.Eventbrite.get')
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

    @patch('documentsManager.utils.Eventbrite.get')
    @patch('documentsManager.utils.Eventbrite.get')
    def test_login_with_Eval_2_accepted(
            self, mock_eventbrite_get, mock_eventbrite_get_2):
        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        mock_eventbrite_get_2.return_value = MOCK_EVENTS_API_2
        new_event_1 = Event.objects.create(
            eb_event_id=50607739110,
            organizer=self.user,
        )
        new_event_2 = Event.objects.create(
            eb_event_id=50607739120,
            organizer=self.user,
        )
        evaluator_1 = Evaluator.objects.create(email='morty@ejemplo.com')
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
        self.client.login(
            email='john@email.com',
            password='john1234',
        )
        response = self.client.get(
            '/accounts/login/',
            follow=True,
        )
        response2 = self.client.get(
            response.context_data['next'],
            follow=True,
            **{'HTTP_REFERER': 'accounts/login'}
        )
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
    def test_evaluator_success_url(
            self,
            mock_get_one_event_api,
            mock_render_to_string):
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

    def setUp(self):
        super(EvaluatorUpdateTest, self).setUp()
        self.event = self.create_event()
        self.evaluator = self.create_evaluator()
        self.evaluator_event = EvaluatorEvent.objects.create(event=self.event, evaluator=self.evaluator)

    def test_evaluator_update_view(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.evaluator.id,
                }
            ),
        )
        self.assertEquals(response.status_code, 200)

    def test_evaluator_update_context(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.evaluator.id,
                }
            ),
        )
        self.assertContains(response, self.event.id)

    def test_evaluator_update_template(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.evaluator.id,
                }
            ),
        )
        self.assertTemplateUsed(response, 'evaluator_form.html')

    def test_evaluator_redirect_on_update(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        data = {
            'name': 'Jack',
            'email': 'test@mail.com',
        }
        response = self.client.post(
            reverse('evaluator_update', kwargs={
                'event_id': self.event.id, 'pk': self.evaluator.id}),
            data
        )
        self.assertRedirects(response, reverse(
            'evaluators', kwargs={'event_id': self.event.id}))

    def test_evaluator_update_success(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = MOCK_EVENTS_API
        data = {
            'name': 'Jack',
            'email': 'test@mail.com',
        }
        response = self.client.post(
            reverse(
                'evaluator_update',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.evaluator.id,
                }
            ),
            data
        )
        self.assertEqual(response.status_code, 302)
        self.evaluator.refresh_from_db()
        self.assertEqual(self.evaluator.name, 'Jack')
        self.assertEqual(self.evaluator.email, 'test@mail.com')


@patch('documentsManager.views.get_one_event_api')
class DocDeleteTest(TestBase):
    def setUp(self):
        super(DocDeleteTest, self).setUp()
        self.event = self.create_event()
        self.file_doc = FileDoc.objects.create(event=self.event)
        self.text_doc = TextDoc.objects.create(event=self.event)

    def test_text_doc_delete_view(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        self.client.get(
            reverse(
                'delete-textdoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.text_doc.id,
                }
            ),
        )
        response = self.client.post(
            reverse(
                'delete-textdoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.text_doc.id,
                }
            ),
        )
        self.assertRedirects(
            response,
            reverse(
                'docs',
                kwargs={'event_id': self.event.id}
            )
        )

    def test_file_doc_delete_view(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        self.client.get(
            reverse(
                'delete-filedoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.file_doc.id,
                }
            ),
        )
        response = self.client.post(
            reverse(
                'delete-filedoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.file_doc.id,
                }
            ),
        )
        self.assertRedirects(
            response,
            reverse(
                'docs',
                kwargs={'event_id': self.event.id}
            )
        )


@patch('documentsManager.views.get_one_event_api')
class DocUpdateTest(TestBase):
    def setUp(self):
        super(DocUpdateTest, self).setUp()
        self.event = self.create_event()
        self.file_doc = FileDoc.objects.create(event=self.event, name='prueba')
        self.text_doc = TextDoc.objects.create(event=self.event, name='prueba')

    def test_text_doc_update_view(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        self.client.get(
            reverse(
                'edit-textdoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.text_doc.id,
                }
            ),
        )
        data = {
            'name': 'CV',
            'is_optional': 'on',
            'measure': 'Words',
            'min': '200',
            'max': '300',
        }
        response = self.client.post(
            reverse(
                'edit-textdoc',
                kwargs={
                    'event_id': self.event.id,
                    'pk': self.text_doc.id,
                }
            ),
            data,
        )
        self.assertEqual(response.status_code, 302)
        self.text_doc.refresh_from_db()
        self.assertEqual(self.text_doc.name, 'CV')


@patch('documentsManager.views.get_one_event_api')
class EvaluatorDeleteTest(TestBase):

    def setUp(self):
        super(EvaluatorDeleteTest, self).setUp()
        self.event = self.create_event()
        self.evaluator = self.create_evaluator()
        self.evaluator_event = EvaluatorEvent.objects.create(event=self.event, evaluator=self.evaluator)

    def test_evaluator_delete_view(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': self.event.id,
                    'evaluator_id': self.evaluator.id,
                }
            ),
        )
        self.assertEquals(response.status_code, 200)

    def test_evaluator_delete_context(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': self.event.id,
                    'evaluator_id': self.evaluator.id,
                }
            ),
        )
        self.assertContains(response, self.event.id)
        # self.assertContains(response, self.evaluator.id)
        # self.assertContains(response, self.evaluator_event.id)

    def test_evaluator_delete_template(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': self.event.id,
                    'evaluator_id': self.evaluator.id,
                }
            ),
        )
        self.assertTemplateUsed(response, 'evaluator_confirm_delete.html')

    def test_evaluator_success_redirect(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.post(
            reverse(
                'evaluator_delete',
                kwargs={
                    'event_id': self.event.id,
                    'evaluator_id': self.evaluator.id,
                }
            ),
        )
        self.assertRedirects(response, reverse(
            'evaluators',
            kwargs={'event_id': self.event.id}
        ))

    def test_evaluator_dissapear_from_db(self, mock_get_one_event_api):
        self.client.post(
            reverse('evaluator_delete', kwargs={
                'event_id': self.event.id, 'evaluator_id': self.evaluator.id}),
        )
        self.assertFalse(EvaluatorEvent.objects.filter(evaluator=self.evaluator, event=self.event).exists())


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


class EvaluatorCreateReview(TestBase):
    def setUp(self):
        super(EvaluatorCreateReview, self).setUp()
        self.event = self.create_event()
        self.evaluator = self.create_evaluator()
        EvaluatorEvent.objects.create(
            event=self.event,
            evaluator=self.evaluator,
            status='accepted',
        )
        file_doc = FileDoc.objects.create(event=self.event, name='name_prueba')
        text_doc = TextDoc.objects.create(event=self.event, description='description_prueba')
        file = File(open('runtime.txt', 'rb'))
        attendee = Attendee.objects.create(
            email='prueba@ejemplo.com',
            name='John Doe'
        )
        file_submission = FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=self.event,
            attendee=attendee
        )
        text_submission = TextSubmission.objects.create(
            text_doc=text_doc,
            content='content',
            event=self.event,
            attendee=attendee
        )
        self.file = Submission.objects.get(id=file_submission.submission_ptr_id)
        self.text = Submission.objects.get(id=text_submission.submission_ptr_id)
        User.objects.create_superuser(
            email='john@email.com',
            password='john1234',
        )
        self.client.login(
            email='john@email.com',
            password='john1234',
        )

    def test_evaluator_approve_file_submission(self):
        r = {
            'approve': 'Approve',
        }
        self.client.post(
            reverse(
                'review',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.file.id,
                }
            ),
            r,
        )
        review = Review.objects.filter(evaluator=self.evaluator, submission=self.file).first()
        self.assertTrue(review.aproved)

    def test_evaluator_reject_file_submission(self):
        r = {
            'reject': 'Reject',
        }
        self.client.post(
            reverse(
                'review',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.file.id,
                }
            ),
            r,
        )
        review = Review.objects.filter(evaluator=self.evaluator, submission=self.file).first()
        self.assertFalse(review.aproved)
        self.assertEqual(self.file.filesubmission.description(), 'name_prueba')

    def test_evaluator_reject_text_submission(self):
        r = {
            'reject': 'Reject',
        }
        self.client.post(
            reverse(
                'review',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.text.id,
                }
            ),
            r,
        )
        review = Review.objects.filter(evaluator=self.evaluator, submission=self.text).first()
        self.assertFalse(review.aproved)
        self.assertEqual(self.text.textsubmission.description(), 'description_prueba')

    @patch('documentsManager.views.get_one_event_api')
    def test_review_view_file_submission(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        self.client.login(email='john@email.com', password='john1234')
        response = self.client.get(
            reverse(
                'review',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.file.id,
                }
            ),
        )
        self.assertEqual(response.context_data['evaluator'], self.evaluator)


class OrganizerSubmission(TestBase):
    def setUp(self):
        super(OrganizerSubmission, self).setUp()
        self.event = self.create_event()
        self.evaluator = self.create_evaluator()
        EvaluatorEvent.objects.create(
            event=self.event,
            evaluator=self.evaluator,
            status='accepted',
        )
        file_doc = FileDoc.objects.create(event=self.event, name='name_prueba')
        text_doc = TextDoc.objects.create(event=self.event, description='description_prueba')
        file = File(open('runtime.txt', 'rb'))
        attendee = Attendee.objects.create(
            email='prueba@ejemplo.com',
            name='John Doe'
        )
        file_submission = FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=self.event,
            attendee=attendee
        )
        text_submission = TextSubmission.objects.create(
            text_doc=text_doc,
            content='content',
            event=self.event,
            attendee=attendee
        )
        self.file = Submission.objects.get(id=file_submission.submission_ptr_id)
        self.text = Submission.objects.get(id=text_submission.submission_ptr_id)
        User.objects.create_superuser(
            email='john@email.com',
            password='john1234',
        )

    @patch('documentsManager.views.get_one_event_api')
    def test_filesubmission(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'submission',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.file.id,
                }
            ),
        )
        self.assertEqual(response.context_data['object'].id, self.file.id)

    @patch('documentsManager.views.get_one_event_api')
    def test_textsubmission(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        response = self.client.get(
            reverse(
                'submission',
                kwargs={
                    'event_id': self.event.id,
                    'submission_id': self.text.id,
                }
            ),
        )
        self.assertEqual(response.context_data['object'].id, self.text.id)


class AcceptInvitationViewTest(TestBase):
    @patch('documentsManager.views.render_to_string')
    def test_accept_invitation_state(self, mock_render_to_string):
        mock_render_to_string.return_value = render_to_string('empty.html', {})
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator_event = EvaluatorEvent.objects.create(
            event=event, evaluator=evaluator)
        self.client.get(
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
        self.client.get(
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

    def test_is_not_valid_EvaluationDateForm_1(self):
        init = datetime.strptime('2018-02-27', '%Y-%m-%d').date()
        end = datetime.strptime('2018-02-25', '%Y-%m-%d').date()
        form3 = EvaluationDateForm({
            'start_evaluation': init,
            'end_evaluation': end,
        })
        result = form3.is_valid()
        self.assertFalse(result)

    def test_is_not_valid_EvaluationDateForm_2(self):
        end = datetime.strptime('2018-02-25', '%Y-%m-%d').date()
        form3 = EvaluationDateForm({
            'end_evaluation': end,
        })
        result = form3.is_valid()
        self.assertFalse(result)

    def test_is_valid_EvaluationDateForm(self):
        init = datetime.strptime('2018-02-20', '%Y-%m-%d').date()
        end = datetime.strptime('2018-02-25', '%Y-%m-%d').date()
        form3 = EvaluationDateForm({
            'start_evaluation': init,
            'end_evaluation': end,
        })
        result = form3.is_valid()
        self.assertTrue(result)

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
        text_doc = TextDoc.objects.create(event=event, name='example')
        key = '{}_text'.format(text_doc.id)
        text_fields = {
            key: 'a a a a a a a a a a'
        }
        result = validate_text_submissions(text_fields)
        self.assertTrue(result)
        self.assertEqual(str(text_doc), 'example')

    def test_not_valid_text_submissions(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        text_doc = TextDoc.objects.create(event=event, name='example', max=2, min=1)
        key = '{}_text'.format(text_doc.id)
        text_fields = {
            key: 'a a a a a'
        }
        result = validate_text_submissions(text_fields)
        self.assertFalse(result)

    def test_validate_files_submissions(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        attendee = Attendee.objects.create(
            email='prueba@ejemplo.com',
            name='John Doe'
        )
        file_doc = FileDoc.objects.create(event=event, name='example')
        key = '{}_file'.format(file_doc.id)
        values = {
            key: ''
        }
        result = validate_files_submissions(values, event.id, attendee.id)
        self.assertTrue(result)
        self.assertEqual(str(file_doc), 'example')

    def test_not_valid_files_submissions(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        attendee = Attendee.objects.create(
            email='prueba@ejemplo.com',
            name='John Doe'
        )
        FileDoc.objects.create(event=event, name='example')
        values = {
            'valor': '',
        }
        result = validate_files_submissions(values, event.id, attendee.id)
        self.assertFalse(result)

    def test_Submission_Form_Text(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        text_doc = TextDoc.objects.create(event=event)
        key = '{}_text'.format(text_doc.id)
        attendee = Attendee.objects.create(
            email='leonard@araoz.com',
            name='leonardo araoz',
        )
        attende_code = AttendeeCode.objects.create(
            event=event,
            attendee=attendee,
        )
        form = SubmissionForm({
            key: 'a a a a a a a a a a',
            'code': attende_code.code,
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

    def test_Submission_Form_File(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        key = '{}_file'.format(file_doc.id)
        attendee = Attendee.objects.create(
            email='leonard@araoz.com',
            name='leonardo araoz',
        )
        attende_code = AttendeeCode.objects.create(
            event=event,
            attendee=attendee,
        )
        form = SubmissionForm(
            files={
                key: '',
            },
            data={
                'code': attende_code.code,
                'event_id': event.id,
                'attendee_id': attendee.id,
            },
        )
        self.assertEqual(form.is_valid(), True)


class FileSubmissionTest(TestBase):

    def test_create_a_file_submission(self):
        event = Event.objects.create(eb_event_id=123, organizer=self.user)
        file_doc = FileDoc.objects.create(event=event)
        file = File(open('runtime.txt', 'rb'))
        attendee = Attendee.objects.create(
            email='prueba@ejemplo.com',
            name='John Doe'
        )
        file_submission = FileSubmission.objects.create(
            file_doc=file_doc,
            file=file,
            event=event,
            attendee=attendee
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


class UtilsTest(TestBase):
    def test_social_user_exists_not_valid(self):
        result = social_user_exists(1)
        self.assertEqual(result, False)

    def test_social_user_exists_valid(self):
        result = social_user_exists(self.auth.uid)
        self.assertEqual(result, True)

    def test_get_data_utils_invalid(self):
        body = {
            'config': {
                'user_id': 1
            },
            'api_url': 'http://algo.com',
        }
        result = get_data(body, 'http://algo.com')
        expected = {
            'status': False,
            'email': False,
        }
        self.assertEqual(result, expected)

    def test_webhook_available_to_process_invalid(self):
        result = webhook_available_to_process(1)
        self.assertEqual(result, False)

    def test_webhook_available_to_process(self):
        result = webhook_available_to_process(self.auth.uid)
        self.assertEqual(result, True)

    def test_get_social_user_not_valid(self):
        result = get_social_user(1)
        expected = None
        self.assertEqual(result, expected)

    def test_get_social_user_valid(self):
        result = get_social_user(self.auth.uid)
        self.assertTrue(isinstance(result, UserSocialAuth))

    def test_send_email_to_attende_not_valid(self):
        context = {
            'host': '',
            'code': 'example',
            'event': 1,
            'id': 1,
        }
        result = send_email_to_attende('', context)
        self.assertEqual(result, 0)

    def test_send_email_to_attende(self):
        context = {
            'host': '',
            'code': 'example',
            'event': 1,
            'id': 1,
        }
        result = send_email_to_attende('familiambc1o@gmail.com', context)
        self.assertEqual(result, 1)

    @patch('documentsManager.utils.create_webhook')
    def test_create_order_webhook_from_view(self, mock):
        mock.return_value = True
        init = UserWebhook.objects.count()
        create_order_webhook_from_view(self.user)
        expected = UserWebhook.objects.count()
        self.assertNotEqual(init, expected)

    def test_get_access_token_form_user_id(self):
        result = get_access_token_form_user_id(self.auth.uid)
        self.assertEqual(result, 'hsadfkjashdbfkjahsdbf')

    def test_get_eventbrite_data(self):
        access_token = settings.SOCIAL_AUTH_EVENTBRITE_KEY
        url = 'https://www.eventbriteapi.com/v3/users/me/events/'
        result = get_eventbrite_data(access_token, url)
        self.assertTrue(isinstance(result, dict))

    @patch('documentsManager.utils.Eventbrite.get')
    def test_get_parsed_event_without_venue(self, mock):
        mock.return_value = MOCK_EVENTS_API
        result = get_parsed_event('access_token', 1)
        self.assertTrue(isinstance(result, dict))

    @patch('documentsManager.utils.Eventbrite.get')
    def test_get_parsed_event_with_venue(self, mock):
        mock.return_value = MOCK_EVENTS_API_2
        result = get_parsed_event('access_token', 1)
        self.assertTrue(isinstance(result, dict))

    def test_create_attendee_code(self):
        init_a = Attendee.objects.count()
        init_ac = AttendeeCode.objects.count()
        event = self.create_event()
        create_attendee_code('leo@leo.com', 'leonardo araoz', event)
        end_a = Attendee.objects.count()
        end_ac = AttendeeCode.objects.count()
        self.assertGreater(end_a, init_a)
        self.assertGreater(end_ac, init_ac)

    def test_create_order_webhook_from_view_wrong(self):
        user = User.objects.create_user('leo@leo.com')
        webhook_id = 1
        UserWebhook.objects.create(
            user=user,
            webhook_id=webhook_id,
        )
        result = UserWebhook.objects.filter(user=user).count()
        create_order_webhook_from_view(user)
        expected = UserWebhook.objects.filter(user=user).count()
        self.assertEqual(result, expected)


class AttendeeCodeTest(TestBase):
    def test_create_attendee_code(self):
        event = self.create_event()
        attendee = Attendee.objects.create(
            email='leonard@araoz.com',
            name='leonardo araoz',
        )
        attende_code = AttendeeCode.objects.create(
            event=event,
            attendee=attendee,
        )
        self.assertEqual(attende_code.available, True)

    def test_send_success_submission_email(self):
        attendee = Attendee.objects.create(
            email='leonardo.araoz.dev@gmail.com',
            name='leonard'
        )
        docs = [{'name': 'example name'}]
        result = send_success_submission_email(attendee, docs)
        self.assertEqual(result, True)

    def test_get_docs_from_event(self):
        event = self.create_event()
        TextDoc.objects.create(
            name='leo',
            event=event,
        )
        result = get_docs_from_event(event)
        self.assertEqual(len(result), 1)

    def test_notify_attendee_from_attende_code(self):
        event = self.create_event()
        TextDoc.objects.create(
            name='leo',
            event=event,
        )
        attendee_code = AttendeeCode.objects.create(
            event=event,
            attendee=Attendee.objects.create(
                email='leo@leo.com',
                name='leo',
            )
        )
        notify_attendee_from_attende_code(attendee_code.code)
        attendee_updated = AttendeeCode.objects.get(id=attendee_code.id)
        self.assertEqual(attendee_updated.available, False)
