import datetime

from django.db import models


class Event(models.Model):
    eb_event_id = models.TextField()
    init_submission = models.DateField(default=datetime.date.today)
    end_submission = models.DateField(blank=True, null=True)


class FileType(models.Model):
    name = models.CharField(max_length=5)
    description = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Doc(models.Model):
    name = models.CharField(max_length=100)
    file_type = models.ForeignKey(FileType)
    is_optional = models.BooleanField(default=True)
    event = models.ForeignKey(Event, blank=True)
