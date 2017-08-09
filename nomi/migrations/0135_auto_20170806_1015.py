# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-06 10:15
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('nomi', '0134_deratification'),
    ]

    operations = [
        migrations.AddField(
            model_name='deratification',
            name='deratify_approvals',
            field=models.ManyToManyField(blank=True, related_name='deratify_approvals', to='nomi.Post'),
        ),
        migrations.AlterField(
            model_name='deratification',
            name='name',
            field=models.ForeignKey(max_length=30, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='deratification',
            name='status',
            field=models.CharField(choices=[('safe', 'safe'), ('requested', 'requested'), ('deratified', 'deratified')], default='safe', max_length=10),
        ),
    ]