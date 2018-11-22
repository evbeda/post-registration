from re import template
from django.urls import reverse
from django.utils.html import format_html
import django_tables2 as tables
from .models import Submission, Review
from documentsManager.models import EvaluatorEvent


class SubmissionsTable(tables.Table):

    requirement = tables.Column(
        verbose_name='Requirement',
        orderable=True,
        empty_values=(),
    )

    reviews = tables.Column(
        verbose_name='Reviews',
        orderable=True,
        empty_values=(),
    )

    evaluators = tables.Column(
        verbose_name='Evaluators',
        orderable=False,
        empty_values=(),
    )

    actions = tables.Column(
        verbose_name=('Actions'),
        orderable=False,
        empty_values=(),
    )

    def __init__(self, data=None, is_organizer=False, *args, **kwargs):
        super(SubmissionsTable, self).__init__(data, *args, **kwargs)
        self.is_organizer = is_organizer

    def render_state(self, value):
        badge_style = ''
        if value == 'Pending':
            badge_style = 'badge-secondary'
        elif value == 'Accepted':
            badge_style = 'badge-success'
        elif value == 'Rejected':
            badge_style = 'badge-danger'
        elif value == '':
            badge_style = 'badge-info'
        return format_html('<span class="badge ' + badge_style + '">' + value + '</span>')

    def render_requirement(self, value, record):
        file_doc = record.filesubmission.file_doc.name
        return file_doc

    def render_reviews(self, record):
        reviews_count = Review.objects.filter(submission=record).count()
        return reviews_count

    def render_evaluators(self, value, record):
        evaluator_events = EvaluatorEvent.objects.filter(
            event=record.event)
        evaluator_list = []
        for evaluator_event in evaluator_events:
            evaluator_list.append(evaluator_event.evaluator)
        return evaluator_list

    def render_actions(self, value, record):
        submission_url = reverse('submission', kwargs={
            'event_id': record.event.id, 'submission_id': record.id})
        close_url = reverse('close_submission', kwargs={
            'event_id': record.event.id, 'submission_id': record.id})
        close_btn = reverse('review', kwargs={
            'event_id': record.event.id, 'submission_id': record.id})
        if self.is_organizer:
            action_btn = '<span class="eds-icon-button eds-icon-button--active eds-icon-button--brand"><a href="' + close_url + \
                '"><button class="eds-btn--button eds-btn--none eds-btn--icon-only" type="button"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><img src="/static/images/justice-hammer.svg" alt="Hammer"></i></button></a></span>'
        else:
            action_btn = '<span class="eds-icon-button eds-icon-button--active eds-icon-button--brand"><a href="' + close_btn + \
                '"><button class="eds-btn--button eds-btn--none eds-btn--icon-only" type="button"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><img src="/static/images/justice-hammer.svg" alt="Hammer"></i></button></a></span>'
        return format_html(action_btn + '<span class="eds-icon-button eds-icon-button--active eds-icon-button--brand"><a href="' + submission_url + '"><button class="eds-btn--button eds-btn--none eds-btn--icon-only" type="button"><i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true"><svg id="eds-icon--eye_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24"><path id="eds-icon--eye_base" fill-rule="evenodd" clip-rule="evenodd" fill="#231F20" d="M11.9 6.5C6.4 6.5 2 12.7 2 12.7s4.4 6.2 9.9 6.2 9.9-6.2 9.9-6.2-4.4-6.2-9.9-6.2zm0 11.3c-3.9 0-7.4-3.6-8.6-5.1 1.2-1.5 4.7-5.1 8.6-5.1 3.9 0 7.4 3.6 8.6 5.1-1.2 1.5-4.7 5.1-8.6 5.1"></path><path id="eds-icon--eye_circle" fill-rule="evenodd" clip-rule="evenodd" fill="#231F20" d="M11.9 9.1c-1.9 0-3.5 1.6-3.5 3.6s1.5 3.6 3.5 3.6 3.5-1.6 3.5-3.6-1.6-3.6-3.5-3.6zm0 6.1c-1.4 0-2.5-1.1-2.5-2.6 0-1.4 1.1-2.6 2.5-2.6s2.5 1.1 2.5 2.6-1.1 2.6-2.5 2.6z"></path></svg></i></button></a></span>'
                           + '<span class="eds-icon-button eds-icon-button--active eds-icon-button--brand"><a href="' + record.filesubmission.file.url +
                           '">    <button class="eds-btn--button eds-btn--none eds-btn--icon-only" type="button">        <i class="eds-vector-image eds-icon--small" data-spec="icon" aria-hidden="true">            <svg id="eds-icon--download_svg" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">                <path id="eds-icon--download_base" fill="#231F20" d="M16 16v1h5v4H3v-4h5v-1H2v6h20v-6z"></path>                <path fill-rule="evenodd" clip-rule="evenodd" fill="#231F20" d="M17.3 11.4l-4.8 4.7V2h-1v14.1l-4.8-4.7-.7.7 6 5.9 6-5.8z"></path>            </svg>        </i>    </button></a></span>'
                           )

    class Meta:
        model = Submission
        template_name = 'partials/submissions_table.html'
        fields = ('id', 'state', 'date',)
        sequence = ('state', 'id', 'date', 'requirement',
                    'reviews', 'evaluators', 'actions')
        show_header = True
        empty_text = 'There are no submissions from your attendees yet.'
