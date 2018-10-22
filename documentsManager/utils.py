from eventbrite import Eventbrite
import requests
import json
# from django.conf import settings
from social_django.models import UserSocialAuth
from .models import UserWebhook
from .app_settings import (
    URL_ENDPOINT,
    WH_ACTIONS,
)


def get_data(body):
    config_data = body
    user_id = config_data['config']['user_id']
    url_user = config_data['api_url']
    if webhook_available_to_process(user_id):
        social_user = get_social_user(user_id)
        access_token = social_user.access_token
        data = requests.get(url_user + '?token=' + access_token)
        container_mail = json.loads(data.content)
        email = (container_mail)['email']
        return {'status': False, 'email': email}
    else:
        return {'status': False, 'email': False}


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
    social_user = UserSocialAuth.objects.filter(
        uid=user_id
    )
    if len(social_user) == 0:
        return False
    else:
        return True


def get_social_user(user_id):
    social_user = UserSocialAuth.objects.filter(
        uid=user_id
    )
    return social_user[0]


def get_social_user_id(user_id):
    social_user = get_social_user(user_id)
    return social_user.user_id


def get_auth_token(user):
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        return ''
    return token


def webhook_available_to_process(user_id):
    if UserSocialAuth.objects.exists() and social_user_exists(user_id):
        return True
