# -*- coding: utf-8 -*-
import hashlib
import json

import requests
from django.core import mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from eventbrite import Eventbrite
from social_django.models import UserSocialAuth

from post_registration.settings import EMAIL_HOST_USER
from .app_settings import (
    URL_ENDPOINT,
    WH_ACTIONS,
)
from .models import UserWebhook, Event, AttendeeCode


def get_data(body, domain):
    user_id = body['config']['user_id']
    url_base = body['api_url']
    response = {
        'status': False,
        'email': False,
    }
    if webhook_available_to_process(user_id):
        access_token = get_access_token_form_user_id(user_id)
        eventbrite_response = get_eventbrite_data(access_token, url_base)
        parsed_event = get_parsed_event(access_token, eventbrite_response['event_id'])
        event_local = Event.objects.get(eb_event_id=parsed_event['eb_id'])
        code = create_code_from_url(url_base)
        email = eventbrite_response['email']
        context = {
            'host': domain,
            'code': code,
            'event': parsed_event,
            'id': event_local.id
        }
        send_email_to_attende(email, context)
        response = {
            'status': True,
            'email': email,
        }
    return response


def create_code_from_url(url_base):
    code_hashed = hashlib.md5(url_base.encode('utf-8'))
    code = code_hashed.hexdigest()
    AttendeeCode.objects.create(code=code)
    return code


def get_access_token_form_user_id(user_id):
    social_user = get_social_user(user_id)
    access_token = social_user.access_token
    return access_token


def get_parsed_event(access_token, evb_id):
    from documentsManager.views import get_one_event_api
    from documentsManager.views import parse_events
    event_data = get_one_event_api(access_token, evb_id)[0]
    parsed_event = parse_events([event_data])[0]
    return parsed_event


def get_eventbrite_data(access_token, url_base):
    complete_url = url_base + '?token=' + access_token
    data = requests.get(complete_url)
    return json.loads(data.content)


def create_order_webhook_from_view(user):
    if not UserWebhook.objects.filter(user=user).exists():
        from documentsManager.views import get_auth_token
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
