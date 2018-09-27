from django.utils.translation import gettext_lazy as _
from django.forms import ModelForm
from .models import Doc


class DocForm(ModelForm):
    class Meta:
        model = Doc
        fields = {'name', 'file_type', 'is_optional'}
        labels = {
            'name': _('Name'),
            'file_type': _('File Format'),
            'is_optional': _('Optional'),
        }
