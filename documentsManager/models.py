import datetime
from django.core.validators import MaxValueValidator
from django.db import models


class Event(models.Model):
    eb_event_id = models.TextField(unique=True)
    init_submission = models.DateField(default=datetime.date.today)
    end_submission = models.DateField(null=True)

    class Meta(object):
        db_table = 'Event'


class FileType(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100, blank=True)

    class Meta(object):
        db_table = 'FileType'

    def __str__(self):
        return self.name + ' (' + self.description + ')'


class FileDoc(models.Model):
    name = models.CharField(max_length=100, blank=False)
    file_type = models.ManyToManyField(FileType)
    quantity = models.PositiveSmallIntegerField(default=1, validators=[
        MaxValueValidator(99)
    ])
    is_optional = models.BooleanField(default=False)
    event = models.ForeignKey(Event, blank=True)

    @property
    def file_types(self):
        return self.file_type.all()

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = 'FileDoc'


class TextDoc(models.Model):
    MEASUREMENT_CHOICE = (
        ('Words', 'Words'),
        ('Characters', 'Characters'),
    )
    name = models.CharField(max_length=100, blank=False)
    description = models.CharField(blank=True, max_length=150)
    is_optional = models.BooleanField(default=False)
    measure = models.CharField(
        max_length=10,
        choices=MEASUREMENT_CHOICE,
        default='Words',
    )
    max = models.PositiveSmallIntegerField(default=500)
    min = models.PositiveSmallIntegerField(default=10)
    event = models.ForeignKey(Event, blank=True)

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = 'TextDoc'
