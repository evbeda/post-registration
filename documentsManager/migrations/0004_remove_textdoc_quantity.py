# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-10-08 14:41
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documentsManager', '0003_merge_20181004_1727'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='textdoc',
            name='quantity',
        ),
    ]
