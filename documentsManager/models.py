# -*- coding: utf-8 -*-
import datetime
import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):

    email = models.EmailField(_('email address'), unique=True)
    username = models.TextField(default=email)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()


class Event(models.Model):
    eb_event_id = models.TextField(unique=True)
    init_submission = models.DateField(default=datetime.date.today)
    end_submission = models.DateField(null=True)
    organizer = models.ForeignKey(User, blank=False)

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


class Submission(models.Model):
    STATES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('evaluated', 'Evaluated'),
    )
    state = models.CharField(max_length=20, choices=STATES, default='pending')
    date = models.DateField(default=datetime.date.today)
    eb_user_id = models.CharField(max_length=100, null=False)

    class Meta(object):
        db_table = 'Submission'


class FileSubmission(Submission):
    file = models.FileField()
    file_doc = models.ForeignKey(FileDoc)

    def description(self):
        return self.file_doc.name

    class Meta(object):
        db_table = 'FileSubmission'


class TextSubmission(Submission):
    text_doc = models.ForeignKey(TextDoc)
    content = models.TextField()

    def description(self):
        return self.text_doc.description

    class Meta(object):
        db_table = 'TextSubmission'


class Evaluator(models.Model):
    name = models.CharField(max_length=20)
    email = models.EmailField(unique=True)
    event = models.ManyToManyField(Event, through='EvaluatorEvent')

    def __str__(self):
        return self.name

    class Meta(object):
        db_table = 'Evaluator'


class EvaluatorEvent(models.Model):
    STATES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    evaluator = models.ForeignKey(Evaluator, on_delete=models.CASCADE)
    state = models.CharField(max_length=20, choices=STATES, default='pending')
    invitation_code = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        db_table = 'EvaluatorEvent'


class Review(models.Model):
    evaluator = models.ForeignKey(Evaluator)
    event = models.ForeignKey(Event)
    date_time = models.DateTimeField(
        default=datetime.datetime.now, editable=False)
    aproved = models.BooleanField(unique=True)

    class Meta:
        db_table = 'Review'


class UserWebhook(models.Model):
    webhook_id = models.CharField(max_length=255)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
