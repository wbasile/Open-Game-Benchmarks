# -*- coding: utf-8 -*-
# Generated by Django 1.9.1 on 2016-03-18 17:45
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lgbdb', '0017_auto_20160318_1516'),
    ]

    operations = [
        migrations.AlterField(
            model_name='useravatar',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
