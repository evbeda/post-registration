from django.forms import ModelForm, ModelMultipleChoiceField, CheckboxSelectMultiple
from django.utils.translation import gettext_lazy as _

from .models import FileDoc, FileType, TextDoc


class FileDocForm(ModelForm):
    file_type = ModelMultipleChoiceField(
        queryset=FileType.objects.all(),
        required=False,
        widget=CheckboxSelectMultiple
    )

    class Meta:
        model = FileDoc
        fields = {
            'name',
            'is_optional',
            'file_type',
        }
        labels = {
            'name': _('Name'),
            'file_type': _('File Format'),
            'is_optional': _('Optional'),
        }


class TextDocForm(ModelForm):
    class Meta:
        model = TextDoc
        fields = {
            'name',
            'is_optional',
            'measure',
            'min',
            'max',
        }
        labels = {
            'name': _('Name'),
            'is_optional': _('Optional'),
            'measure': _('Measure'),
            'min': _('Minimum'),
            'max': _('Maximum'),
        }
