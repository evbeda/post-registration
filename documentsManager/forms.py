# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.auth.forms import UserCreationForm
from django.core.mail import EmailMultiAlternatives
from django.forms import (
    CheckboxInput,
    CheckboxSelectMultiple,
    EmailField,
    Form,
    ModelForm,
    ModelMultipleChoiceField,
    NumberInput,
    Select,
    TextInput,
    Textarea,
    DateInput,
    EmailInput,
)
from django.template.base import logger
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _

from .models import (
    Evaluator,
    Event,
    FileDoc,
    FileType,
    TextDoc,
    User,
    EvaluatorEvent,
    Review,
    Result,
    Submission,
)
from .utils import (
    notify_attendee_from_attende_code,
    validate_files_submissions,
    validate_text_submissions,
)


class FileDocForm(ModelForm):
    file_type = ModelMultipleChoiceField(
        queryset=FileType.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple()
    )

    class Meta:
        model = FileDoc
        fields = [
            'name',
            'is_optional',
            'file_type',
            'quantity',
        ]
        labels = {
            'name': _('Name'),
            'file_type': _('Allowed Format'),
            'is_optional': _('Optional'),
            'quantity': _('Quantity'),
        }
        widgets = {
            'quantity': TextInput(
                attrs={
                    'min': '1',
                    'max': '100',
                    'type': 'number',
                    'class': 'form-control col-3'}),
            'name': TextInput(
                attrs={
                    'class': 'form-control col-10'}),
            'is_optional': CheckboxInput(
                attrs={
                    'class': 'form-check-input'}),
        }


class TextDocForm(ModelForm):

    def is_valid(self):
        valid = super(TextDocForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data['min'] >= self.cleaned_data['max']:
            self.add_error('max', 'Max cannot be less than min.')
            return False
        return True

    class Meta:
        model = TextDoc
        fields = [
            'name',
            'description',
            'is_optional',
            'measure',
            'min',
            'max',
        ]
        labels = {
            'name': _('Name'),
            'description': _('Description'),
            'is_optional': _('Optional'),
            'measure': _('Measure'),
            'min': _('Minimum'),
            'max': _('Maximum'),
        }
        widgets = {
            'name': TextInput(
                attrs={
                    'class': 'form-control col-10'}),
            'description': Textarea(
                attrs={
                    'rows': 3,
                    'class': 'form-control'}),
            'is_optional': CheckboxInput(
                attrs={
                    'class': 'form-check-input'}),
            'measure': Select(
                attrs={
                    'class': 'form-control'}),
            'min': NumberInput(
                attrs={
                    'class': 'form-control'}),
            'max': NumberInput(
                attrs={
                    'class': 'form-control'}),
        }


class EventForm(ModelForm):
    def is_valid(self):
        valid = super(EventForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data['init_submission'] >= self.cleaned_data['end_submission']:
            self.add_error(
                'end_submission',
                'End date cannot be less than Init date of Submissions .')
            return False
        return True

    class Meta:
        model = Event
        fields = [
            'init_submission',
            'end_submission',
        ]
        widgets = {
            'init_submission': TextInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': datetime.now().strftime('%Y-%m-%d'),
            }),
            'end_submission': TextInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
        }


class EvaluationDateForm(ModelForm):

    def is_valid(self):
        valid = super(EvaluationDateForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data['start_evaluation'] >= self.cleaned_data['end_evaluation']:
            self.add_error(
                'end_evaluation',
                'End date cannot be less than start date of Evaluations .')
            return False
        return True

    class Meta:
        model = Event
        fields = [
            'start_evaluation',
            'end_evaluation'
        ]
        widgets = {
            'start_evaluation': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'min': datetime.now().strftime('%Y-%m-%d'),
            }),
            'end_evaluation': DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
            }),
        }


class SignUpForm(UserCreationForm):
    email = EmailField(required=True)

    class Meta:
        model = User
        fields = {
            'password1',
            'password2',
            'email',
        }

        labels = {
            'password1': _('Password'),
            'password2': _('Confirm Password'),
            'email': _('Email'),
        }

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = user.email
        if commit:
            user.save()
        return user


class SubmissionForm(Form):

    def is_valid(self):
        if not self.data.get('code'):
            return True
        files_validation = True
        if len(self.files):
            files_validation = validate_files_submissions(
                self.files,
                self.data.get('event_id'),
                self.data.get('attendee_id'),
            )
        text_validation = validate_text_submissions(
            self.data,
            self.data.get('event_id'),
            self.data.get('attendee_id'),
        )
        if files_validation and text_validation:
            notify_attendee_from_attende_code(self.data.get('code'))
        return files_validation and text_validation


class EvaluatorForm(ModelForm):
    class Meta:
        model = Evaluator
        fields = [
            'name',
            'email',
        ]
        widgets = {
            'name': TextInput(attrs={'class': 'form-control'}),
            'email': EmailInput(attrs={'class': 'form-control'}),
        }

    def send_email(self, form, event, accept_url, decline_url):
        email = form.cleaned_data['email']
        invitation_code = EvaluatorEvent.objects.filter(
            event=event['id']).values_list('invitation_code', flat=True)
        FROM = 'kaizendev18@gmail.com'
        TO = email
        SUBJECT = 'Invitation to evaluate submissions for an event.'
        html_content = render_to_string('email/evaluation_request.html', {
            'event': event,
            'invitation_code': invitation_code[0].hex,
            'accept_url': accept_url,
            'decline_url': decline_url,
        })
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(SUBJECT, text_content, FROM, [TO])
        msg.attach_alternative(html_content, "text/html")
        try:
            msg.send()
        except Exception as e:
            logger.exception(e)

    def save(self, update=True, event_id=None):
        evaluator = super().save()
        if not update:
            event = Event.objects.get(pk=event_id)
            EvaluatorEvent.objects.create(event=event, evaluator=evaluator)
            evaluator.save()
        return evaluator

    def validate_unique(self):
        pass


class ReviewForm(ModelForm):

    class Meta:
        model = Review
        fields = [
            'justification',
        ]
        labels = {
            'justification': _('Justification'),
        }
        widgets = {
            'justification': Textarea(
                attrs={
                    'rows': 6,
                    'class': 'form-control',
                },
            ),
        }

    def is_valid(self):
        valid = super(ReviewForm, self).is_valid()
        if not valid:
            return valid
        return True


class ResultForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super(ResultForm, self).__init__(*args, **kwargs)
        self.is_approved = None
        self.submission_id = None

    class Meta:
        model = Result
        fields = ['justification']
        widgets = {
            'justification': Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-control',
                },
            ),
        }

    def save(self):
        result = super(ResultForm, self).save(commit=False)
        result.approved = self.is_approved
        submission = Submission.objects.get(id=self.submission_id)
        submission.state = 'accepted' if self.is_approved else 'rejected'
        submission.save()
        result.submission = submission
        return result.save()

class ResultUpdateForm(ModelForm):

    class Meta:
        model = Result
        fields = ['justification', 'approved']
        widgets = {
            'justification': Textarea(
                attrs={
                    'rows': 4,
                    'class': 'form-control',
                },
            ),
        }
