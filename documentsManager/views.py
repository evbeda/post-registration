# -*- coding: utf-8 -*-
import json
from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import (
    FormView,
    CreateView,
    DeleteView,
    UpdateView,
    ListView,
)
from django.views.generic.base import TemplateView
from eventbrite import Eventbrite
from multi_form_view import MultiFormView
from social_django.models import UserSocialAuth

from .forms import (
    EvaluatorForm,
    EventForm,
    FileDocForm,
    TextDocForm,
    SignUpForm,
    SubmissionForm,
)
from .models import (
    FileDoc,
    Event,
    TextDoc,
    Evaluator,
    EvaluatorEvent,
    FileSubmission,
)
from .utils import (
    get_data,
    create_order_webhook_from_view,
)


@csrf_exempt
def accept_webhook(request):
    get_data(json.loads(request.body), request.build_absolute_uri)
    return HttpResponse()


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


@method_decorator(login_required, name='dispatch')
class DocFormView(MultiFormView, LoginRequiredMixin):
    template_name = 'doc_form.html'
    form_classes = {
        'file_doc': FileDocForm,
        'text_doc': TextDocForm,
    }

    def get_initial(self):
        self.file_form = True
        return super(DocFormView, self).get_initial()

    def get_context_data(self, **kwargs):
        context = super(DocFormView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        context['pr_event_id'] = event.id
        eb_event = get_one_event_api(get_auth_token(
            self.request.user), event.eb_event_id)
        view_event = parse_events(eb_event)
        event = view_event[0]
        event['id'] = event_id
        context['event'] = event
        context['file_form'] = self.file_form
        return context

    def post(self, request, **kwargs):
        if request.POST.get('submit_file'):
            self.file_form = True
            form = FileDocForm(request.POST)
        elif request.POST.get('submit_text'):
            self.file_form = False
            form = TextDocForm(request.POST)
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
        if 'submit_file' in form.data.keys():
            form.save_m2m()  # needed since using commit=False
        return new_doc


@method_decorator(login_required, name='dispatch')
class DocsView(FormView, LoginRequiredMixin):
    template_name = 'docs.html'
    form_class = EventForm

    def get_context_data(self, **kwargs):
        context = super(DocsView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        context['event_model'] = event
        context['form'] = EventForm(initial={
            'init_submission': event.init_submission,
            'end_submission': event.end_submission,
        })
        eb_event = get_one_event_api(get_auth_token(
            self.request.user), event.eb_event_id)
        view_event = parse_events(eb_event)
        event = view_event[0]
        event['eb_event_start'] = eb_event[0]['start']['utc']
        event['id'] = event_id
        context['event'] = event
        context['docs_file'] = FileDoc.objects.filter(event__id=event_id)
        context['docs_text'] = TextDoc.objects.filter(event__id=event_id)
        context['attendee_url'] = self.request.get_host() + reverse(
            'landing',
            kwargs={
                'event_id': event_id
            },)
        return context

    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        update_dates(self.request, self.kwargs['event_id'])
        return HttpResponseRedirect(reverse('docs', kwargs={'event_id': self.kwargs['event_id']}))


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        self.accepted_events = evaluator_events(request)
        if self.request.META.get('HTTP_REFERER') is None:
            prev_page = 'none'
        else:
            prev_page = self.request.META.get('HTTP_REFERER')
        if (len(self.accepted_events) == 1) and (prev_page.find('accounts/login') != (-1)):
            event_id = self.accepted_events[0]['event_id']
            return redirect(reverse('submissionHome', kwargs={'event_id': event_id}))
        else:
            return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        create_order_webhook_from_view(self.request.user,)
        context['user'] = self.request.user
        context['is_eb_user'] = self.request.user.social_auth.exists()
        context['events_to_evaluate'] = self.accepted_events
        if context['is_eb_user']:
            api_events_w_venues = get_events_with_venues_api(
                get_auth_token(self.request.user))
            parse_api_events = parse_events(api_events_w_venues)
            docs_events_list = Event.objects.all().values_list('eb_event_id', 'id')
            events = filter_managed_event(parse_api_events, docs_events_list)
            context['events'] = events
        return context


class BaseDocUpdate(UpdateView):

    def get_context_data(self, **kwargs):
        context = super(UpdateView, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        return context

    def get_success_url(self):
        return reverse(
            'docs',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


class FileDocUpdate(BaseDocUpdate):
    model = FileDoc
    form_class = FileDocForm
    template_name = 'file_doc_update_form.html'


class TextDocUpdate(BaseDocUpdate):
    model = TextDoc
    form_class = TextDocForm
    template_name = 'text_doc_update_form.html'


class BaseDocDelete(DeleteView):
    template_name = 'doc_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super(DeleteView, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        return context

    def get_success_url(self):
        return reverse(
            'docs',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


class FileDocDelete(BaseDocDelete):
    model = FileDoc
    success_url = '/'


class TextDocDelete(BaseDocDelete):
    model = TextDoc
    success_url = '/'


class SuccessView(TemplateView):
    template_name = 'success.html'


class LandingView(FormView):
    template_name = 'landing_form.html'
    success_url = '/success/'
    form_class = SubmissionForm

    def get_context_data(self, **kwargs):
        context = super(LandingView, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        event = Event.objects.filter(pk=event_id).first()
        if event:
            context['event'] = event
            eb_event = get_one_event_api(
                get_auth_token(self.request.user),
                event.eb_event_id
            )
            context['eb_event'] = parse_events(eb_event)[0]
            text_docs = TextDoc.objects.filter(event=event)
            if text_docs:
                context['text_docs'] = text_docs
            file_docs = FileDoc.objects.filter(event=event)
            if file_docs:
                context['file_docs'] = file_docs
        return context


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = 'signup.html'

    def get_success_url(self):
        return reverse(
            'login',
        )


@method_decorator(login_required, name='dispatch')
class EvaluatorList(TemplateView):
    template_name = 'evaluators_grid.html'

    def get_context_data(self, **kwargs):
        context = super(EvaluatorList, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        eb_event = get_one_event_api(
            get_auth_token(self.request.user),
            event.eb_event_id
        )
        view_event = parse_events(eb_event)
        context['event'] = view_event[0]
        context['event_id'] = event_id
        context['evaluator_events'] = EvaluatorEvent.objects.filter(event=event).select_related('evaluator')
        return context


@method_decorator(login_required, name='dispatch')
class EvaluatorCreate(CreateView):
    model = Evaluator
    template_name = 'evaluator_form.html'
    form_class = EvaluatorForm

    def get_context_data(self, **kwargs):
        context = super(EvaluatorCreate, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        return context

    def form_valid(self, form):
        form.save()
        form.send_email(form)
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        return reverse(
            'evaluators',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


@method_decorator(login_required, name='dispatch')
class EvaluatorUpdate(UpdateView):
    model = Evaluator
    template_name = 'evaluator_form.html'
    form_class = EvaluatorForm

    def get_context_data(self, **kwargs):
        context = super(EvaluatorUpdate, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        return context

    def get_success_url(self):
        return reverse(
            'evaluators',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


@method_decorator(login_required, name='dispatch')
class EvaluatorDelete(DeleteView):
    model = Evaluator
    template_name = 'evaluator_confirm_delete.html'

    def get_context_data(self, **kwargs):
        context = super(EvaluatorDelete, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        return context

    def get_success_url(self):
        return reverse(
            'evaluators',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


class SubmissionView(TemplateView, LoginRequiredMixin):
    template_name = 'submission.html'

    def get_context_data(self, **kwargs):
        context = super(SubmissionView, self).get_context_data(**kwargs)
        return context


class SubmissionsList(ListView, LoginRequiredMixin):
    model = FileSubmission
    template_name = 'filesubmission_list.html'

    def get_context_data(self, **kwargs):
        context = super(SubmissionsList, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        our_event = Event.objects.get(id=event_id)
        eb_event = get_one_event_api(
            get_auth_token(self.request.user),
            our_event.eb_event_id,
        )
        view_event = parse_events(eb_event)
        ev_count = EvaluatorEvent.objects.filter(
            event=our_event,
            state='accepted'
        ).count()
        context['evaluators_cont'] = ev_count
        context['event'] = view_event[0]
        context['event_id'] = event_id
        return context


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
            view_event['venue'] = event.get('venue', {}).get('address', {}).get('localized_address_display', None)
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
    return eventbrite.get(path='/users/me/events/', expand=('venue',)).get('events', [])


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
    return HttpResponseRedirect(reverse('docs', kwargs={'event_id': new_event.id}))


def add_event(eb_event_id, end_submission, organizer):
    new_event = Event(eb_event_id=eb_event_id, end_submission=end_submission, organizer=organizer)
    new_event.save()
    return new_event


def update_dates(request, event_id):
    event = Event.objects.get(id=event_id)
    event.init_submission = request.POST['init_submission']
    event.end_submission = request.POST['end_submission']
    event.save()
    return HttpResponseRedirect(reverse('docs', kwargs={'event_id': event_id}))


def evaluator_events(request):
    evaluators = Evaluator.objects.filter(email=request.user.email)
    accepted_eval_event = []
    event_list = []
    accepted_events = []
    for evaluator in evaluators:
        accepted = EvaluatorEvent.objects.filter(evaluator_id=evaluator.id, state='accepted')
        if len(accepted):
            accepted_eval_event.append(accepted)
    for event in accepted_eval_event:
        event_list.append(Event.objects.filter(id=event[0].event_id))
    for event in event_list:
        auth_user = UserSocialAuth.objects.get(user_id=event[0].organizer_id)
        token = auth_user.extra_data['access_token']
        eb_event = get_one_event_api(
            token,
            event[0].eb_event_id
        )
        accepted_events.append(parse_events(eb_event)[0])
    if len(accepted_events) != 0:
        for ev in accepted_events:
            eb_event_id = ev['eb_id']
            event = Event.objects.get(eb_event_id=eb_event_id)
            ev['event_id'] = event.id
    return accepted_events
