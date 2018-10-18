from datetime import datetime
from django.forms import (
    CheckboxSelectMultiple,
    ModelForm,
    ModelMultipleChoiceField,
    TextInput,
    NumberInput,
    CheckboxInput,
    Select,
)
from django.utils.translation import gettext_lazy as _

from .models import FileDoc, FileType, TextDoc, Event


class FileDocForm(ModelForm):
    # error_css_class = 'error'
    # required_css_class = 'required'

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
            'file_type': _('File Format'),
            'is_optional': _('Optional'),
            'quantity': _('Quantity'),
        }
        widgets = {
            'quantity': TextInput(attrs={'min': '1', 'max': '100', 'type': 'number', 'class': 'form-control col-3'}),
            'name': TextInput(attrs={'class': 'form-control col-10'}),
            'is_optional': CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TextDocForm(ModelForm):
    # error_css_class = 'error'
    # required_css_class = 'required'

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
            'is_optional',
            'measure',
            'min',
            'max',
        ]
        labels = {
            'name': _('Name'),
            'is_optional': _('Optional'),
            'measure': _('Measure'),
            'min': _('Minimum'),
            'max': _('Maximum'),
        }
        widgets = {
            'name': TextInput(attrs={'class': 'form-control col-10'}),
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
