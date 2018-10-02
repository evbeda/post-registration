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
        api_events = get_all_events_api(get_auth_token(self.request.user))
        eb_events = parse_events(api_events)
        events_id_list = Event.objects.all().values_list('eb_event_id', flat=True)
        view_events = filter_no_managed_event(eb_events, events_id_list)
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

    def get_context_data(self, **kwargs):
        context = super(DocFormView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        eb_event = get_one_event_api(get_auth_token(self.request.user), event.eb_event_id)
        view_event = parse_events(eb_event)
        event = view_event[0]
        event['id'] = event_id
        context['event'] = event
        return context

    def post(self, request, *args, **kwargs):
        form = DocForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.add_doc(form, self.kwargs['event_id'])
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

    def get_context_data(self, **kwargs):
        context = super(DocsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        eb_event = get_one_event_api(get_auth_token(self.request.user), event.eb_event_id)
        view_event = parse_events(eb_event)
        event = view_event[0]
        event['id'] = event_id
        context['event'] = event
        context['docs'] = Doc.objects.filter(event__id=event_id)
        return context


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        api_events = get_all_events_api(get_auth_token(self.request.user))
        parse_api_events = parse_events(api_events)
        docs_events_list = Event.objects.all().values_list('eb_event_id', 'id')
        events = filter_managed_event(parse_api_events, docs_events_list)
        context['events'] = events
        return context


def parse_events(api_events):
    events = []
    for event in api_events:
        view_event = {
            'eb_id': event['id'],
            'name': event['name']['text'],
            'start': datetime.strptime(event['start']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
            'end': datetime.strptime(event['end']['utc'], '%Y-%m-%dT%H:%M:%SZ'),
        }
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
