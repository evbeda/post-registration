# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-06 17:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='review',
            name='event',
        ),
        migrations.AddField(
            model_name='review',
            name='submission',
            field=models.ForeignKey(
                default=1,
                on_delete=django.db.models.deletion.CASCADE,
                to='documentsManager.Submission'),
            preserve_default=False,
        ),
    ]