# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-14 16:30
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomi', '0067_auto_20170614_1540'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='contact',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]