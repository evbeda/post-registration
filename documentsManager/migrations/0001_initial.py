# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-26 15:21
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Doc',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('is_optional', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('eb_event_id', models.TextField()),
                ('init_submission', models.DateField(default=datetime.date.today)),
                ('end_submission', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='FileType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=5)),
                ('description', models.CharField(blank=True, max_length=100)),
            ],
        ),
        migrations.AddField(
            model_name='doc',
            name='event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='documentsManager.Event'),
        ),
        migrations.AddField(
            model_name='doc',
            name='file_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='documentsManager.FileType'),
        ),
    ]
