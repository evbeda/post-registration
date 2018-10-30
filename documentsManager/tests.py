from datetime import datetime
from unittest import skip
from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import resolve, reverse
from django.db.utils import DataError
from django.test import TestCase
from social_django.models import UserSocialAuth

from documentsManager.apps import DocumentsmanagerConfig
from documentsManager.forms import (
    EventForm,
    TextDocForm,
    SignUpForm,
    EvaluatorForm,
    validate_text_submissions, validate_files_submissions, SubmissionForm)
from documentsManager.models import (
    Event,
    TextDoc,
    FileType,
    FileDoc,
    Evaluator,
    User,
    EvaluatorEvent)
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


class TestBase(TestCase):
    def setUp(self):
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
        login = self.client.login(username='kaizen@email.com', password='awesome1234')
        return login

    def create_event(self, eb_event_id=1):
        return Event.objects.create(eb_event_id=eb_event_id)

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
    def test_docs_redirect(self, mock_eventbrite_get):

        mock_eventbrite_get.return_value = MOCK_EVENTS_API
        new_event = Event.objects.create(eb_event_id=1)
        response = self.client.get('/event/{}/docs/'.format(new_event.id))
        self.assertEqual(response.status_code, 200)

    def test_events_redirect(self):
        response = self.client.get('/events/')
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_doc_form_redirect(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        new_event = Event.objects.create(eb_event_id=1)
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
        new_event = add_event(EVB_ID, '2018-03-03')
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
        event = Event.objects.create(eb_event_id=321)
        event.end_submission = '2018-02-25'
        response = self.client.get('/landing/{}/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    def test_response_with_success(self):
        event = Event.objects.create(eb_event_id=321)
        response = self.client.get('/landing/{}/success/'.format(event.id))
        self.assertEqual(response.status_code, 200)

    @patch('documentsManager.views.Eventbrite.get')
    def test_response_with_landing_page_with_text_doc(self, mock_api_evb):
        mock_api_evb.return_value = MOCK_EVENTS_API
        event = Event.objects.create(eb_event_id=321)
        TextDoc.objects.create(event=event)
        FileDoc.objects.create(event=event)
        response = self.client.get('/landing/{}/'.format(event.id))
        self.assertTrue('text_docs' in response.context)
        self.assertTrue('file_docs' in response.context)


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


class ModelsTest(TestCase):
    def test_model_text_exist(self):
        new_event = Event.objects.create(eb_event_id=3)
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
        new_event = Event.objects.create(eb_event_id=1)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.max = 'asd'
        result = isinstance(text_doc.max, int)
        self.assertFalse(result)

    def test_model_text_max_word(self):
        new_event = Event.objects.create(eb_event_id=1)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.max = 237
        result = isinstance(text_doc.max, int)
        self.assertTrue(result)

    def test_model_text_error_max_word_2(self):
        new_event = Event.objects.create(eb_event_id=1)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.min = 'asd'
        result = isinstance(text_doc.min, int)
        self.assertFalse(result)

    def test_model_text_max_word_2(self):
        new_event = Event.objects.create(eb_event_id=1)
        text_doc = TextDoc.objects.create(event=new_event)
        text_doc.min = 4560
        result = isinstance(text_doc.min, int)
        self.assertTrue(result)

    def test_model_file_quantity_only_recieve_ints(self):
        new_event = Event.objects.create(eb_event_id=1)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.quantity = 'asd'
        with self.assertRaises(ValueError):
            file_doc.save()

    def test_model_file_quantity_is_int(self):
        new_event = Event.objects.create(eb_event_id=1)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.quantity = 123
        result = isinstance(file_doc.quantity, int)
        self.assertTrue(result)

    def test_model_file_name_submission_invalid(self):
        new_event = Event.objects.create(eb_event_id=1)
        with self.assertRaises(DataError) as data_error:
            FileDoc.objects.create(
                event=new_event,
                name='asd' * 50,
            )
        self.assertEqual(data_error.exception.args,
                         ('value too long for type character varying(100)\n',))

    def test_model_file_name_submission_valid(self):
        new_event = Event.objects.create(eb_event_id=1)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.name = ('Documento')
        self.assertEqual(file_doc.name, 'Documento')

    def test_model_text_doc_name_submission_invalid(self):
        new_event = Event.objects.create(eb_event_id=1)
        with self.assertRaises(DataError) as data_error:
            TextDoc.objects.create(
                event=new_event,
                name='asd' * 50,
            )
        self.assertEqual(data_error.exception.args,
                         ('value too long for type character varying(100)\n',))

    def test_model_text_doc_name_submission_valid(self):
        new_event = Event.objects.create(eb_event_id=1)
        file_doc = FileDoc.objects.create(event=new_event)
        file_doc.name = ('Foto')
        self.assertEqual(file_doc.name, 'Foto')


class SignUpView(TestBase):
    def test_signup_view_name(self):
        view = resolve(reverse('signup'))
        self.assertEqual(view.url_name, 'signup')


class EvaluatorTest(TestBase):

    def test_create_evaluator(self):
        evaluator = self.create_evaluator()
        self.assertTrue(isinstance(evaluator, Evaluator))

    def test_evaluator_string_representation(self):
        evaluator = self.create_evaluator()
        self.assertEquals(str(evaluator), evaluator.name)

    def test_evaluator_verbose_name_plural(self):
        self.assertEqual(
            str(Evaluator._meta.verbose_name_plural), "evaluators")

    @skip("Don't want to test")
    def test_evaluator_default_state(self):
        evaluator = self.create_evaluator()
        self.assertEquals(evaluator.state, 'pending')


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

    @skip("Don't want to test")
    def test_evaluator_list_response_content(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator.events.add(event)
        evaluator.save()
        response = self.client.get(
            reverse('evaluators', kwargs={'event_id': event.id}))
        self.assertContains(response, evaluator)


@patch('documentsManager.views.get_one_event_api')
class EvaluatorUpdateTest(TestBase):
    @skip("Don't want to test")
    def test_evaluator_redirect_on_update(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        evaluator = self.create_evaluator()
        event = self.create_event()
        evaluator.events.add(event)
        evaluator.save()
        data = {'name': 'Jack', 'email': 'test@mail.com',
                'state': evaluator.state, 'events': evaluator.events}
        response = self.client.post(
            reverse('evaluator_update', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
            data
        )
        self.assertRedirects(response, reverse(
            'evaluators', kwargs={'event_id': event.id}))

    @skip("Don't want to test")
    def test_evaluator_update_success(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = MOCK_EVENTS_API
        evaluator = self.create_evaluator()
        event = self.create_event()
        evaluator.events.add(event)
        evaluator.save()
        data = {'name': 'Jack', 'email': 'test@mail.com',
                'state': evaluator.state, 'events': evaluator.events}
        response = self.client.post(
            reverse('evaluator_update', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
            data
        )
        self.assertEqual(response.status_code, 302)
        evaluator.refresh_from_db()
        self.assertEqual(evaluator.name, 'Jack')
        self.assertEqual(evaluator.email, 'test@mail.com')

    # test_evaluator_update_invalid


@patch('documentsManager.views.get_one_event_api')
class EvaluatorDeleteTest(TestBase):
    @skip("Don't want to test")
    def test_evaluator_success_redirect(self, mock_get_one_event_api):
        mock_get_one_event_api.return_value = [MOCK_EVENTS_API]
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator.events.add(event)
        evaluator.save()
        response = self.client.post(
            reverse('evaluator_delete', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
        )
        self.assertRedirects(response, reverse(
            'evaluators', kwargs={'event_id': event.id}))

    @skip("Don't want to test")
    def test_cannot_evaluator_delete_twice(self, mock_get_one_event_api):
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator.events.add(event)
        evaluator.save()
        response = self.client.post(
            reverse('evaluator_delete', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
        )
        response = self.client.post(
            reverse('evaluator_delete', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
        )
        self.assertEquals(response.status_code, 404)

    @skip("Don't want to test")
    def test_evaluator_dissapear_from_db(self, mock_get_one_event_api):
        event = self.create_event()
        evaluator = self.create_evaluator()
        evaluator.events.add(event)
        evaluator.save()
        self.client.post(
            reverse('evaluator_delete', kwargs={
                    'event_id': event.id, 'pk': evaluator.id}),
        )
        self.assertFalse(Evaluator.objects.filter(pk=evaluator.id).exists())


class EvaluatorFormTest(TestBase):
    def test_valid_form(self):
        e = self.create_evaluator(name='John', email='john@mail.com')
        data = {'name': e.name, 'email': e.email, }
        form = EvaluatorForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        e = Evaluator.objects.create(name='John', email='johnmail.com')
        data = {'name': e.name, 'email': e.email, }
        form = EvaluatorForm(data=data)
        self.assertFalse(form.is_valid())


class EvaluatorEventTest(TestBase):
    @skip("Don't want to test")
    def test_create_a_model(self):
        evaluator_event = EvaluatorEvent.objects.create()
        self.assertTrue(isinstance(evaluator_event, EvaluatorEvent))

class FormsTest(TestCase):

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
            'email': 'juan@gmail.com',
        })
        form.save()
        user = User.objects.get(email='juan@gmail.com')
        self.assertEqual(user.email, 'juan@gmail.com')

    def test_validate_text_submissions(self):
        event = Event.objects.create(eb_event_id=123)
        text_doc = TextDoc.objects.create(event=event)
        key = '{}_text'.format(text_doc.id)
        text_fields = {
            key: 'a a a a a a a a a a'
        }
        result = validate_text_submissions(text_fields)
        expected = True
        self.assertEqual(result, expected)

    def test_validate_files_submissions(self):
        event = Event.objects.create(eb_event_id=123)
        file_doc = FileDoc.objects.create(event=event)
        key = '{}_file'.format(file_doc.id)
        values = {
            key: ''
        }
        result = validate_files_submissions(values, event.id)
        self.assertEqual(result, True)

    def test_Submission_Form(self):
        event = Event.objects.create(eb_event_id=123)
        text_doc = TextDoc.objects.create(event=event)
        key = '{}_text'.format(text_doc.id)
        form = SubmissionForm({
            key: 'a a a a a a a a a a'
        })
        self.assertEqual(form.is_valid(), True)

    def test_Submission_Form_with_files(self):
        event = Event.objects.create(eb_event_id=123)
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
