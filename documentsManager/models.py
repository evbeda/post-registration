import datetime

from django.db import models


class Event(models.Model):
    eb_event_id = models.TextField(unique=True)
    init_submission = models.DateField(default=datetime.date.today)
    end_submission = models.DateField(blank=True, null=True)

    class Meta(object):
        db_table = 'Event'


class FileType(models.Model):
    name = models.CharField(max_length=20)
    description = models.CharField(max_length=100, blank=True)

    class Meta(object):
        db_table = 'FileType'

    def __str__(self):
        return self.name


class FileDoc(models.Model):
    name = models.CharField(max_length=100, blank=False)
    file_type = models.ManyToManyField(FileType)
    is_optional = models.BooleanField(default=False)
    event = models.ForeignKey(Event, blank=True)

    @property
    def file_types(self):
        return self.file_type.all()

    class Meta(object):
        db_table = 'FileDoc'


class TextDoc(models.Model):
    MEASUREMENT_CHOICE = (
        ('WORDS', 'Words'),
        ('CHARS', 'Chars'),
    )
    name = models.CharField(max_length=100, blank=False)
    is_optional = models.BooleanField(default=False)
    measure = models.CharField(
        max_length=5,
        choices=MEASUREMENT_CHOICE,
        default='WORDS',
    )
    max = models.IntegerField(default=500)
    min = models.IntegerField(default=0)
    event = models.ForeignKey(Event, blank=True)

    class Meta(object):
        db_table = 'TextDoc'
