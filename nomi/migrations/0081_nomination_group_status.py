# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-23 09:38
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nomi', '0080_auto_20170622_2036'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomination',
            name='group_status',
            field=models.CharField(choices=[('normal', 'normal'), ('grouped', 'grouped')], default='normal', max_length=50),
        ),
    ]