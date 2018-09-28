from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.decorators import method_decorator
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView
from django.http import HttpResponseRedirect
from django.urls import reverse
from eventbrite import Eventbrite
from social_django.models import UserSocialAuth

from .forms import DocForm
from .models import Event, Doc


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
        eb_event_id = self.kwargs['event_id']
        return Doc.objects.filter(event__eb_event_id=eb_event_id)

    def get_context_data(self, **kwargs):
        context = super(DocFormView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        url_event = '/events/{}/'.format(self.kwargs['event_id'])
        context['event'] = eventbrite.get(url_event)
        return context

    def post(self, request, *args, **kwargs):
        form = DocForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        new_doc = self.add_doc(form, self.kwargs['event_id'])
        return HttpResponseRedirect(reverse('docs', kwargs={'event_id': new_doc.id}))

    def add_doc(self, form, event_id):
        new_doc = form.save(commit=False)

        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        url_event = '/events/{}/'.format(self.kwargs['event_id'])
        api_event = eventbrite.get(url_event)
        try:
            event = Event.objects.get(
                eb_event_id=api_event['id'],
            )
        except Event.DoesNotExist:
            event = Event.objects.create(
                eb_event_id=api_event['id'],
            )
        new_doc.event = event

        new_doc.save()
        return new_doc


@method_decorator(login_required, name='dispatch')
class DocsView(TemplateView, LoginRequiredMixin):
    template_name = 'docs.html'

    def get_context_data(self, **kwargs):
        context = super(DocsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        token = get_auth_token(self.request.user)
        eventbrite = Eventbrite(token)
        url = '/events/{}/'.format(self.kwargs['event_id'])
        context['event'] = eventbrite.get(url)
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
        error_msg = 'UserSocialAuth does not exists!'
        raise Exception(error_msg)
    return token
