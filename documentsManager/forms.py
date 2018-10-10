from django.forms import (
    CheckboxSelectMultiple,
    ModelForm,
    ModelMultipleChoiceField,
    TextInput,
    ValidationError
)
from django.utils.translation import gettext_lazy as _

from .models import FileDoc, FileType, TextDoc, Event


class FileDocForm(ModelForm):
    # error_css_class = 'error'
    # required_css_class = 'required'

    file_type = ModelMultipleChoiceField(
        queryset=FileType.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple
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
            'quantity': TextInput(attrs={'min': '1', 'max': '100', 'type': 'number'}),
        }


class TextDocForm(ModelForm):
    # error_css_class = 'error'
    # required_css_class = 'required'

    def is_valid(self):
        valid = super(TextDocForm, self).is_valid()
        if not valid:
            return valid
        if (self.cleaned_data['min'] >= self.cleaned_data['max']):
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


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = [
            'init_submission',
            'end_submission',
        ]
        labels = {
            'init_submission': _('Init date of Submissions'),
            'end_submission': _('End date of Submissions'),
        }
        widgets = {
            'init_submission': TextInput(attrs={'type': 'date', 'class': 'form-control mx-2'}),
            'end_submission': TextInput(attrs={'type': 'date', 'class': 'form-control mx-2'}),
        }
