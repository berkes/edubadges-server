# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2018-05-01 12:26
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lti_edu', '0003_resourcelinkbadge'),
    ]

    operations = [
        migrations.AddField(
            model_name='lticlient',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
