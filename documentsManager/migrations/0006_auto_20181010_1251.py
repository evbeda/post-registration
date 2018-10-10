# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-10 12:51
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0005_auto_20181009_1314'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filedoc',
            name='quantity',
            field=models.PositiveSmallIntegerField(validators=[django.core.validators.MaxValueValidator(99)]),
        ),
        migrations.AlterField(
            model_name='textdoc',
            name='max',
            field=models.PositiveSmallIntegerField(default=500),
        ),
        migrations.AlterField(
            model_name='textdoc',
            name='min',
            field=models.PositiveSmallIntegerField(default=10),
        ),
    ]
