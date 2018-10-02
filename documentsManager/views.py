from datetime import datetime
from django.http import HttpResponseRedirect

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from .forms import DocForm
from .models import Doc, Event
from eventbrite import Eventbrite
from social_django.models import UserSocialAuth


@method_decorator(login_required, name='dispatch')
class EventsView(TemplateView, LoginRequiredMixin):
    template_name = 'events.html'

    def get_context_data(self, **kwargs):
        context = super(EventsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        api_events = eventbrite.get('/users/me/events/').get('events', [])
        eb_events = parse_events(api_events)
        events_id_list = Event.objects.all().values_list('eb_event_id', flat=True)
        print(events_id_list)
        view_events = []
        for eb_event in eb_events:
            if (eb_event['eb_id'] not in events_id_list):
                view_events.append(eb_event)
        context['events'] = view_events
        return context

    def dispatch(self, request, *args, **kwargs):
        if self.request.method == 'GET' and 'eb_event_id' in self.kwargs.keys():
            eb_event_id = self.kwargs['eb_event_id']
            new_event = self.add_event(eb_event_id)
            return HttpResponseRedirect(reverse('docs', kwargs={'event_id': new_event.id}))

        return super(EventsView, self).dispatch(request, *args, **kwargs)

    def add_event(self, eb_event_id):
        new_event = Event(eb_event_id=eb_event_id)
        new_event.save()
        return new_event


@method_decorator(login_required, name='dispatch')
class DocFormView(FormView, LoginRequiredMixin):
    template_name = 'doc_form.html'
    form_class = DocForm

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        return Doc.objects.filter(event_id__eb_event_id=event_id)

    def get_context_data(self, **kwargs):
        context = super(DocFormView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        url = '/events/{}/'.format(event.eb_event_id)
        eb_event = eventbrite.get(url)
        view_event = {
            'id': event.id,
            'eb_id': eb_event['id'],
            'name': eb_event['name']['text'],
            # 2018-11-01T22:00:00Z
            'start': datetime.strptime(eb_event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            # 2018-11-01T22:00:00Z
            'end': datetime.strptime(eb_event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
        }
        context['event'] = view_event
        return context

    def post(self, request, *args, **kwargs):
        form = DocForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        new_doc = self.add_doc(form, self.kwargs['event_id'])
        return HttpResponseRedirect(reverse('docs', kwargs={'event_id': self.kwargs['event_id']}))

    def add_doc(self, form, event_id):
        new_doc = form.save(commit=False)
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        new_doc.event = event
        new_doc.save()
        return new_doc


@method_decorator(login_required, name='dispatch')
class DocsView(TemplateView, LoginRequiredMixin):
    template_name = 'docs.html'

    def get_queryset(self):
        event_id = self.kwargs['event_id']
        return Doc.objects.filter(event_id__=event_id)

    def get_context_data(self, **kwargs):
        context = super(DocsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        url = '/events/{}/'.format(event.eb_event_id)
        eb_event = eventbrite.get(url)
        view_event = {
            'id': event.id,
            'eb_id': eb_event['id'],
            'name': eb_event['name']['text'],
            # 2018-11-01T22:00:00Z
            'start': datetime.strptime(eb_event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            # 2018-11-01T22:00:00Z
            'end': datetime.strptime(eb_event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
        }
        context['event'] = view_event
        context['docs'] = Doc.objects.filter(event__id=event_id)
        return context


def parse_events(api_events):
    events = []
    for event in api_events:
        view_event = {
            'eb_id': event['id'],
            'name': event['name']['text'],
            # 2018-11-01T22:00:00Z
            'start': datetime.strptime(event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            # 2018-11-01T22:00:00Z
            'end': datetime.strptime(event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
        }
        events.append(view_event)
    return events


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
        error_msg = 'UserSocialAuth does not exists!'
        raise Exception(error_msg)
    return token
