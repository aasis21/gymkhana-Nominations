# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-19 10:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0008_auto_20170614_1605'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filledform',
            name='data',
            field=models.CharField(blank=True, max_length=30000, null=True),
        ),
    ]