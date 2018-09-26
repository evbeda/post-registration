from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from eventbrite import Eventbrite
from social_django.models import UserSocialAuth
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import datetime


@method_decorator(login_required, name='dispatch')
class EventsView(TemplateView, LoginRequiredMixin):
    template_name = 'events.html'

    def get_context_data(self, **kwargs):
        context = super(EventsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        context['events'] = self.get_user_events(eventbrite)
        return context

    def get_user_events(self, eventbrite):
        events = []
        api_events = eventbrite.get('/users/me/events/').get('events', [])
        for event in api_events:
            view_event = {
                'id': event['id'],
                'name': event['name']['text'],
                # 2018-11-01T22:00:00Z
                'start': datetime.strptime(event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
                # 2018-11-01T22:00:00Z
                'end': datetime.strptime(event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            }
            events.append(view_event)
        return events


@method_decorator(login_required, name='dispatch')
class DocFormView(TemplateView, LoginRequiredMixin):
    template_name = 'doc_form.html'

    def get_context_data(self, **kwargs):
        context = super(DocFormView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        pepito = self.request.GET['id']
        pepe = '/events/{}/'.format(pepito)
        context['event'] = eventbrite.get(pepe)
        return context


def get_auth_token(user):
    """
    This method will receive an user and
    return its repesctive social_auth token
    """
    try:
        token = user.social_auth.get(
            provider='eventbrite'
        ).access_token
    except UserSocialAuth.DoesNotExist:
        print('UserSocialAuth does not exists!')
    return token
