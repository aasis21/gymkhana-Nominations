# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-27 09:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nomi', '0015_auto_20170527_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='nomination',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='nomi.Nomination'),
        ),
    ]