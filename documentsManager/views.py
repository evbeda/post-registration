# -*- coding: utf-8 -*-


from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import MultipleObjectsReturned
from django.core.mail import EmailMultiAlternatives
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.template.base import logger
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.html import strip_tags
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    FormView,
    DetailView,
    UpdateView,
)
from django.views.generic.base import TemplateView
from django_filters.views import FilterView
from django_tables2.views import SingleTableMixin
from multi_form_view import MultiFormView

from documentsManager.utils import (
    evaluator_events,
    parse_events,
    get_auth_token,
    get_all_events_api,
    get_events_with_venues_api,
    get_one_event_api,
    filter_managed_event,
    filter_no_managed_event,
    update_dates,
    get_access_token_of_event,
    send_evaluator_decision_to_organizer)
from .filters import SubmissionFilter
from .forms import (
    EvaluatorForm,
    EventForm,
    FileDocForm,
    TextDocForm,
    SignUpForm,
    SubmissionForm,
    EvaluationDateForm,
    ReviewForm,
    ResultForm,
)
from .models import (
    AttendeeCode,
    Evaluator,
    EvaluatorEvent,
    Event,
    FileDoc,
    Review,
    Submission,
    TextDoc,
    Result,
)
from .tables import (
    SubmissionsTable,
    SubmissionsTableOrganizer,
    SubmissionsTableEvaluator,
)
from .utils import (
    create_order_webhook_from_view,
)


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
        return HttpResponseRedirect(
            reverse(
                'docs', kwargs={
                    'event_id': self.kwargs['event_id']}))

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
            'preview',
            kwargs={
                'event_id': event_id
            }, )
        return context

    def post(self, request, *args, **kwargs):
        form = EventForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        update_dates(self.request, self.kwargs['event_id'])
        return HttpResponseRedirect(
            reverse(
                'docs', kwargs={
                    'event_id': self.kwargs['event_id']}))


@method_decorator(login_required, name='dispatch')
class HomeView(TemplateView, LoginRequiredMixin):
    template_name = 'home.html'

    def dispatch(self, request, *args, **kwargs):
        self.accepted_events = evaluator_events(request)
        if self.request.META.get('HTTP_REFERER') is None:
            prev_page = 'none'
        else:
            prev_page = self.request.META.get('HTTP_REFERER')
        if (len(self.accepted_events) == 1) and (
                prev_page.find('accounts/login') != (-1)):
            event_id = self.accepted_events[0]['event_id']
            return redirect(
                reverse(
                    'submissions', kwargs={
                        'event_id': event_id}))
        return super(HomeView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        context['user'] = self.request.user
        context['is_eb_user'] = self.request.user.social_auth.exists()
        context['events_to_evaluate'] = self.accepted_events
        if context['is_eb_user']:
            create_order_webhook_from_view(self.request.user)
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

    def dispatch(self, request, *args, **kwargs):
        is_preview = 'preview' in request.path
        if not is_preview:
            code = self.kwargs['code']
            try:
                attende_code = AttendeeCode.objects.get(code=code)
            except MultipleObjectsReturned:
                return redirect(reverse('success'))
            if not attende_code.available:
                return redirect(reverse('success'))
        return super(LandingView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(LandingView, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        event = Event.objects.filter(pk=event_id).first()
        if 'code' in self.kwargs:
            context['code'] = self.kwargs['code']
            context['attendee'] = AttendeeCode.objects.get(code=self.kwargs['code']).attendee
        if event:
            context['event'] = event
            eb_event = get_one_event_api(
                get_access_token_of_event(event),
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
class EvaluatorList(FormView, LoginRequiredMixin):
    template_name = 'evaluators_grid.html'
    form_class = EvaluationDateForm

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
        context['event_model'] = event
        context['evaluator_events'] = EvaluatorEvent.objects.filter(
            event=event).select_related('evaluator')
        context['form'] = EvaluationDateForm(initial={
            'start_evaluation': event.start_evaluation,
            'end_evaluation': event.end_evaluation,
        })
        return context

    def post(self, request, *args, **kwargs):
        form = EvaluationDateForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        event_id = self.kwargs['event_id']
        event = Event.objects.get(id=event_id)
        event.start_evaluation = self.request.POST['start_evaluation']
        event.end_evaluation = self.request.POST['end_evaluation']
        event.save()
        return HttpResponseRedirect(
            reverse(
                'evaluators', kwargs={
                    'event_id': event_id}))


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
        event_id = self.kwargs['event_id']
        event = Event.objects.get(pk=event_id)
        try:
            evaluator = Evaluator.objects.get(email=form.cleaned_data['email'])
            EvaluatorEvent.objects.create(
                evaluator=evaluator, event=event)
        except Evaluator.DoesNotExist:
            evaluator = form.save(update=False, event_id=event_id)
        evaluator_event = EvaluatorEvent.objects.get(
            event=event, evaluator=evaluator)
        eb_event = get_one_event_api(get_auth_token(
            self.request.user), event.eb_event_id)
        parsed_event = parse_events(eb_event)
        accept_url = self.request.build_absolute_uri(
            reverse('accept-invitation', kwargs={'invitation_code': evaluator_event.invitation_code}))
        decline_url = self.request.build_absolute_uri(
            reverse('decline-invitation', kwargs={'invitation_code': evaluator_event.invitation_code}))
        parsed_event[0]['id'] = event_id
        form.send_email(form, parsed_event[0], accept_url, decline_url)
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

    def form_valid(self, form):
        event_id = self.kwargs['event_id']
        form.save(update=True, event_id=event_id)
        return super(EvaluatorUpdate, self).form_valid(form)

    def get_success_url(self):
        return reverse(
            'evaluators',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )


@method_decorator(login_required, name='dispatch')
class EvaluatorDelete(DeleteView):
    model = EvaluatorEvent
    template_name = 'evaluator_confirm_delete.html'

    def get_object(self):
        pk = EvaluatorEvent.objects.get(
            event=self.kwargs['event_id'],
            evaluator=self.kwargs['evaluator_id']
        ).pk
        self.kwargs['pk'] = pk
        return super(EvaluatorDelete, self).get_object()

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


class SubmissionsList(SingleTableMixin, FilterView):
    table_class = SubmissionsTable
    model = Submission
    template_name = 'submissions.html'
    filterset_class = SubmissionFilter

    def get_context_data(self, **kwargs):
        context = super(SubmissionsList, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        event = Event.objects.get(id=event_id)
        user_id = self.request.user.id
        is_organizer = user_id == event.organizer.id
        if (is_organizer):
            context['is_organizer'] = True
        if self.request.user.social_auth.exists():
            token = get_auth_token(self.request.user)
        else:
            token = get_access_token_of_event(event)
            evaluator = Evaluator.objects.get(email=self.request.user.email)
        eb_event = get_one_event_api(token, event.eb_event_id)
        context['event'] = parse_events(eb_event)[0]
        context['evaluators_cont'] = EvaluatorEvent.objects.filter(
            event=event,
            status='accepted',
        ).count()
        if self.request.GET:
            filter = SubmissionFilter(
                self.request.GET,
                queryset=Submission.objects.filter(event_id=event_id),
            )
            if is_organizer:
                table = SubmissionsTableOrganizer(
                    filter.qs,
                    is_organizer=is_organizer,
                )
            else:
                table = SubmissionsTableEvaluator(
                    filter.qs,
                    is_organizer=is_organizer,
                    evaluator=evaluator,
                )
        else:
            if is_organizer:
                table = SubmissionsTableOrganizer(
                    Submission.objects.filter(event_id=event_id),
                    is_organizer=is_organizer,
                )
            else:
                table = SubmissionsTableEvaluator(
                    Submission.objects.filter(event_id=event_id),
                    is_organizer=is_organizer,
                    evaluator=evaluator,
                )
        context['table'] = table
        return context


@method_decorator(login_required, name='dispatch')
class SubmissionView(DetailView, LoginRequiredMixin):
    model = Submission
    template_name = 'submission.html'
    pk_url_kwarg = 'submission_id'

    def get_context_data(self, **kwargs):
        context = super(SubmissionView, self).get_context_data(**kwargs)
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        event = Event.objects.get(id=event_id)
        token = get_access_token_of_event(event)
        eb_event = get_one_event_api(token, event.eb_event_id)
        context['event'] = parse_events(eb_event)[0]
        context['reviews'] = Review.objects.filter(
            submission_id=self.object.id
        )
        submission = Submission.objects.get(id=self.kwargs['submission_id'])
        try:
            submission.textsubmission
            context['submission_type'] = 'TEXT'
        except submission.DoesNotExist:
            submission.filesubmission
            context['submission_type'] = 'FILE'
        return context


@method_decorator(login_required, name='dispatch')
class ReviewView(FormView, LoginRequiredMixin):
    form_class = ReviewForm
    template_name = 'review.html'

    def get_context_data(self, **kwargs):
        context = super(ReviewView, self).get_context_data(**kwargs)
        context['evaluator'] = Evaluator.objects.filter(
            email=self.request.user.email).first()
        context['submissions'] = Submission.objects.filter(
            event_id=self.kwargs['submission_id']).first()
        event_id = self.kwargs['event_id']
        context['event_id'] = event_id
        event = Event.objects.get(id=event_id)
        token = get_access_token_of_event(event)
        eb_event = get_one_event_api(token, event.eb_event_id)
        context['event'] = parse_events(eb_event)[0]
        return context

    def post(self, request, **kwargs):
        if request.POST.get('approve'):
            self.is_aprove = True
        elif request.POST.get('reject'):
            self.is_aprove = False
        form = ReviewForm(request.POST)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.add_review(form)
        return HttpResponseRedirect(
            reverse(
                'submissions', kwargs={
                    'event_id': self.kwargs['event_id']}))

    def add_review(self, form):
        new_review = form.save(commit=False)
        new_review.submission = Submission.objects.get(
            id=self.kwargs['submission_id'])
        new_review.evaluator = Evaluator.objects.get(
            email=self.request.user.email)
        new_review.approved = self.is_aprove
        new_review.save()
        send_evaluator_decision_to_organizer(self.kwargs['event_id'], new_review)
        return


class AcceptInvitationView(TemplateView):
    template_name = "thanks.html"

    def get_context_data(self, **kwargs):
        context = super(AcceptInvitationView, self).get_context_data(**kwargs)
        invitation_code = self.kwargs['invitation_code']
        evaluator_event = EvaluatorEvent.objects.get(
            invitation_code=invitation_code)
        evaluator_event.status = 'accepted'
        evaluator_event.save()
        evaluator = Evaluator.objects.get(pk=evaluator_event.evaluator.id)
        event = Event.objects.get(pk=evaluator_event.event.id)
        FROM = 'kaizendev18@gmail.com'
        TO = event.organizer.email
        SUBJECT = 'A new Evaluator for your event has accepted.'
        html_content = render_to_string('email/new_evaluator.html', {
            'evaluator': evaluator})
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(
            SUBJECT, text_content, FROM, [TO])
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except Exception as e:
            logger.exception(e)
        return context


class DeclineInvitationView(View):
    def get(self, request, *args, **kwargs):
        invitation_code = self.kwargs['invitation_code']
        evaluator_event = EvaluatorEvent.objects.get(
            invitation_code=invitation_code)
        evaluator_event.status = 'rejected'
        evaluator_event.save()
        return HttpResponse('GET request!')


class ResultCreate(CreateView):
    model = Result
    template_name = 'result_form.html'
    form_class = ResultForm

    def post(self, request, **kwargs):
        form = ResultForm(request.POST)
        submission_id = self.kwargs['submission_id']
        if form.is_valid():
            form.submission_id = submission_id
            if request.POST.get("approve_btn", ""):
                form.is_approved = True
            elif request.POST.get("reject_btn", ""):
                form.is_approved = False
            else:
                form.is_approved = None

            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse(
            'submissions',
            kwargs={
                'event_id': self.kwargs['event_id'],
            },
        )
