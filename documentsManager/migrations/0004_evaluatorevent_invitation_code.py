# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-31 18:07
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0003_auto_20181031_1257'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluatorevent',
            name='invitation_code',
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
