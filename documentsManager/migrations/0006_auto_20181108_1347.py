# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-08 13:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0005_auto_20181108_1344'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='end_evaluation',
            field=models.DateField(blank=True, null=True),
        ),
    ]
