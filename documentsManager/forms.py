from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm, ModelMultipleChoiceField, CheckboxSelectMultiple
from .models import Doc, FileType


class DocForm(ModelForm):
    file_type = ModelMultipleChoiceField(queryset=FileType.objects.all(),
                                         required=False, widget=CheckboxSelectMultiple)

    class Meta:
        model = Doc
        fields = {'name', 'is_optional', 'file_type'}
        labels = {
            'name': _('Name'),
            'file_type': _('File Format'),
            'is_optional': _('Optional'),
        }
