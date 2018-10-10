# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-10 13:27
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0007_merge_20181010_1309'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filedoc',
            name='quantity',
            field=models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MaxValueValidator(99)]),
        ),
    ]
