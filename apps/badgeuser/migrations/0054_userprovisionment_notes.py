# Generated by Django 2.2.9 on 2020-06-09 12:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0053_populate_badgeuser_institution'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprovisionment',
            name='notes',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
