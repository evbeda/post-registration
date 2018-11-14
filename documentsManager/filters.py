import django_filters
from .models import Submission


class SubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = Submission
        fields = ['state']
