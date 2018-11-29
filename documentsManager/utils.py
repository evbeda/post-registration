# -*- coding: utf-8 -*-
import json
from datetime import datetime
from itertools import chain

import requests
from django.core import mail
from django.http import HttpResponseRedirect, HttpResponse
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags
from django.views.decorators.csrf import csrf_exempt
from eventbrite import Eventbrite
from social_django.models import UserSocialAuth

from post_registration.settings import EMAIL_HOST_USER
from .app_settings import (
    URL_ENDPOINT,
    WH_ACTIONS,
)
from .models import (
    TextDoc,
    FileDoc,
    FileSubmission,
    Evaluator,
    EvaluatorEvent,
    TextSubmission,
    UserWebhook,
    Event,
    AttendeeCode,
    Attendee,
)


def get_data(body, domain):
    user_id = body['config']['user_id']
    url_base = body['api_url']
    response = {
        'status': False,
        'email': False,
    }
    if webhook_available_to_process(user_id):
        access_token = get_access_token_form_user_id(user_id)
        eventbrite_response = get_eventbrite_data(
            access_token,
            url_base,
        )
        parsed_event = get_parsed_event(
            access_token,
            eventbrite_response['event_id'],
        )
        event_local = Event.objects.get(eb_event_id=parsed_event['eb_id'])
        email = eventbrite_response['email']
        name = eventbrite_response['name']
        attende_code = create_attendee_code(email, name, event_local)
        context = {
            'code': attende_code.code,
            'event': parsed_event,
            'id': event_local.id,
            'host': domain,
            'name': name,
        }
        send_email_to_attende(email, context)
        response = {
            'status': True,
            'email': email,
        }
    return response


def create_attendee_code(email, name, event):
    attende = Attendee.objects.create(
        email=email,
        name=name,
    )
    attende_code = AttendeeCode.objects.create(
        attendee=attende,
        event=event
    )
    return attende_code


def get_access_token_form_user_id(user_id):
    social_user = get_social_user(user_id)
    access_token = social_user.access_token
    return access_token


def get_parsed_event(access_token, evb_id):
    event_data = get_one_event_api(access_token, evb_id)[0]
    parsed_event = parse_events([event_data])[0]
    return parsed_event


def get_eventbrite_data(access_token, url_base):
    complete_url = url_base + '?token=' + access_token
    data = requests.get(complete_url)
    return json.loads(data.content)


def create_order_webhook_from_view(user):
    if not UserWebhook.objects.filter(user=user).exists():
        token = get_auth_token(user)
        webhook_id = create_webhook(token)
        if webhook_id is not None:
            UserWebhook.objects.create(
                user=user,
                webhook_id=webhook_id,
            )


def create_webhook(token):
    data = {
        'endpoint_url': URL_ENDPOINT,
        'actions': WH_ACTIONS,
    }
    response = Eventbrite(token).post('/webhooks/', data)
    return response.get('id', None)


def social_user_exists(user_id):
    social_user = UserSocialAuth.objects.filter(uid=user_id)
    if len(social_user) == 0:
        return False
    return True


def get_social_user(user_id):
    social_user = UserSocialAuth.objects.filter(uid=user_id).first()
    return social_user


def webhook_available_to_process(user_id):
    if UserSocialAuth.objects.exists() and social_user_exists(user_id):
        return True
    return False


def send_email_to_attende(email, context):
    to = email
    subject = 'Documentation Required'
    from_email = EMAIL_HOST_USER
    template_name = 'email/email_attende.html'
    html_message = render_to_string(
        template_name,
        context,
    )
    text_content = strip_tags(html_message)
    mail_sended = mail.send_mail(
        subject,
        text_content,
        from_email,
        [to],
        html_message=html_message
    )
    return mail_sended


def notify_attendee_from_attende_code(code):
    attendee_code = AttendeeCode.objects.get(code=code)
    attendee = Attendee.objects.get(id=attendee_code.attendee.id)
    docs = get_docs_from_event(event=attendee_code.event)
    result = send_success_submission_email(attendee, docs)
    if result:
        attendee_code.available = False
        attendee_code.save()


def get_docs_from_event(event):
    text_docs = TextDoc.objects.filter(event=event)
    file_docs = FileDoc.objects.filter(event=event)
    return list(chain(text_docs, file_docs))


def send_success_submission_email(attendee, docs):
    to = attendee.email
    subject = 'Documentation Submited'
    from_email = EMAIL_HOST_USER
    template_name = 'email/submission_success.html'
    context = {
        'docs': docs
    }
    html_message = render_to_string(
        template_name,
        context,
    )
    text_content = strip_tags(html_message)
    mail_sended = mail.send_mail(
        subject,
        text_content,
        from_email,
        [to],
        html_message=html_message
    )
    return mail_sended


def send_evaluator_decision_to_organizer(event_id, new_review):
    to = Event.objects.get(id=event_id).organizer.email
    context = {
        'review': new_review,
    }
    subject = 'An evaluator made a review'
    from_email = EMAIL_HOST_USER
    template_name = 'email/evaluator_review.html'
    html_message = render_to_string(
        template_name,
        context,
    )
    text_content = strip_tags(html_message)
    return mail.send_mail(
        subject,
        text_content,
        from_email,
        [to],
        html_message=html_message
    )


def validate_files_submissions(files, id_event, attendee_id):
    event = Event.objects.get(pk=id_event)
    file_docs = FileDoc.objects.filter(event=event)
    attendee = Attendee.objects.get(pk=attendee_id)
    for file_doc in file_docs:
        name = '{}_file'.format(file_doc.id)
        if name not in files.keys():
            return False
        FileSubmission.objects.create(
            file_doc=file_doc,
            file=files[name],
            event=event,
            attendee=attendee
        )
    return True


def validate_text_submissions(text_fields, id_event, attende_id):
    event = Event.objects.get(pk=id_event)
    attendee = Attendee.objects.get(pk=attende_id)
    for text_field in text_fields.keys():
        if '_text' in text_field:
            text_id = text_field.replace('_text', '')
            text_doc = TextDoc.objects.get(pk=text_id)
            quantity = len(text_field)
            if text_doc.measure == 'Words':
                quantity = len(text_field.split(' '))
            if not (quantity < text_doc.min or quantity > text_doc.max):
                return False
            text_doc = TextDoc.objects.get(id=text_id)
            TextSubmission.objects.create(
                text_doc=text_doc,
                content=text_fields[text_field],
                event=event,
                attendee=attendee
            )
    return True


def evaluator_events(request):
    evaluator = Evaluator.objects.filter(email=request.user.email)
    event_list = []
    accepted_events = []
    if evaluator:
        accepted_eval_event = EvaluatorEvent.objects.filter(
            evaluator_id=evaluator[0].id, status='accepted')
        for event in accepted_eval_event:
            event_list.append(Event.objects.filter(id=event.event_id))
        for event in event_list:
            token = get_access_token_of_event(event[0])
            eb_event = get_one_event_api(
                token,
                event[0].eb_event_id
            )
            accepted_events.append(parse_events(eb_event)[0])
        if accepted_events:
            for ev in accepted_events:
                eb_event_id = ev['eb_id']
                event = Event.objects.get(eb_event_id=eb_event_id)
                ev['event_id'] = event.id
    return accepted_events


def parse_events(api_events):
    events = []
    for event in api_events:
        view_event = {
            'eb_id': event.get('id', None),
            'name': event.get('name', {}).get('text', 'Unnamed'),
            'start': datetime.strptime(event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            'end': datetime.strptime(event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            'description': event.get('description', {}).get('text', 'No description'),
            'logo': (event.get('logo', {}) or {}).get('original', {}).get('url', None),
            'is_free': event.get('is_free', {}),
            'venue_id': event.get('venue_id', {}),
        }
        if view_event['venue_id']:
            view_event['venue'] = event.get('venue', {}).get(
                'address', {}).get('localized_address_display', None)
        else:
            view_event['venue'] = ''
        events.append(view_event)
    return events


def get_auth_token(user):
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        error_msg = 'UserSocialAuth does not exists!'
        raise Exception(error_msg)
    return token


def get_all_events_api(token):
    eventbrite = Eventbrite(token)
    return eventbrite.get('/users/me/events/').get('events', [])


def get_events_with_venues_api(token):
    eventbrite = Eventbrite(token)
    return eventbrite.get(
        path='/users/me/events/',
        expand=('venue',)).get('events', [])


def get_one_event_api(token, eb_event_id):
    eventbrite = Eventbrite(token)
    one_event = [eventbrite.get('/events/{}/'.format(eb_event_id))]
    return one_event


def filter_managed_event(api_events, model_events):
    events = []
    for api_event in api_events:
        for docs_event in model_events:
            if api_event['eb_id'] in docs_event[0]:
                api_event['id'] = docs_event[1]
                events.append(api_event)
    return events


def filter_no_managed_event(api_events, model_events):
    events = []
    for eb_event in api_events:
        if eb_event['eb_id'] not in model_events:
            events.append(eb_event)
    return events


def select_event(request, eb_event_id):
    eb_event = get_one_event_api(get_auth_token(request.user), eb_event_id)
    view_event = parse_events(eb_event)
    default_end_submission = view_event[0]['start']
    new_event = add_event(eb_event_id, default_end_submission, request.user)
    return HttpResponseRedirect(
        reverse(
            'docs', kwargs={
                'event_id': new_event.id}))


def add_event(eb_event_id, end_submission, organizer):
    new_event = Event(eb_event_id=eb_event_id,
                      end_submission=end_submission, organizer=organizer)
    new_event.save()
    return new_event


def update_dates(request, event_id):
    event = Event.objects.get(id=event_id)
    event.init_submission = request.POST['init_submission']
    event.end_submission = request.POST['end_submission']
    event.save()
    return HttpResponseRedirect(reverse('docs', kwargs={'event_id': event_id}))


def get_access_token_of_event(event):
    auth_user = UserSocialAuth.objects.get(user_id=event.organizer_id)
    return auth_user.extra_data['access_token']


@csrf_exempt
def accept_webhook(request):
    get_data(json.loads(request.body), request.META['URL_LOCAL'])
    return HttpResponse()
