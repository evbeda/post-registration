# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-22 12:53
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0009_auto_20181022_1241'),
    ]

    operations = [
        migrations.AddField(
            model_name='textdoc',
            name='description',
            field=models.CharField(blank=True, max_length=150),
        ),
    ]
