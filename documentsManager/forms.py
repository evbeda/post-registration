# -*- coding: utf-8 -*-
from datetime import datetime

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms import (
    CheckboxSelectMultiple,
    ModelForm,
    ModelMultipleChoiceField,
    TextInput,
    Textarea,
    NumberInput,
    CheckboxInput,
    Select,
    EmailField,
    Form,
)
from django.utils.translation import gettext_lazy as _

from .models import (
    FileDoc,
    FileType,
    TextDoc,
    Event,
    FileSubmission,
)


class FileDocForm(ModelForm):

    file_type = ModelMultipleChoiceField(
        queryset=FileType.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
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
            'quantity': TextInput(attrs={'min': '1', 'max': '100', 'type': 'number', 'class': 'form-control col-3'}),
            'name': TextInput(attrs={'class': 'form-control col-10'}),
            'is_optional': CheckboxInput(attrs={'class': 'form-check-input'}),
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
            'name': TextInput(attrs={'class': 'form-control col-10'}),
            'description': Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'is_optional': CheckboxInput(attrs={'class': 'form-check-input'}),
            'measure': Select(attrs={'class': 'form-control'}),
            'min': NumberInput(attrs={'class': 'form-control'}),
            'max': NumberInput(attrs={'class': 'form-control'}),
        }


class EventForm(ModelForm):
    def is_valid(self):
        valid = super(EventForm, self).is_valid()
        if not valid:
            return valid
        if self.cleaned_data['init_submission'] >= self.cleaned_data['end_submission']:
            self.add_error(
                'end_submission', 'End date cannot be less than Init date of Submissions .')
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


class SignUpForm(UserCreationForm):
    email = EmailField(required=True)

    class Meta:
        model = User
        fields = {
            'username',
            'password1',
            'password2',
            'email',
        }

        labels = {
            'username': _('Username'),
            'password1': _('Password'),
            'password2': _('Confirm Password'),
            'email': _('Email'),
        }

    def save(self, commit=True):
        user = super(SignUpForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class SubmissionForm(Form):

    def is_valid(self):
        if len(self.files):
            event = Event.objects.filter(pk=self.data.get('event_id')).first()
            file_docs = FileDoc.objects.filter(event=event)
            for file_doc in file_docs:
                name = '{}_file'.format(file_doc.id)
                if name in self.files.keys():
                    FileSubmission.objects.create(
                        file_doc=file_doc,
                        file=self.files[name],
                    )
            return True
        return False
