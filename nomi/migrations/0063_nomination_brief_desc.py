# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-14 10:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomi', '0062_remove_nomination_brief_desc'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomination',
            name='brief_desc',
            field=models.TextField(blank=True, max_length=51, null=True),
        ),
    ]
