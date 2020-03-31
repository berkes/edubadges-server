# Generated by Django 2.2.9 on 2020-03-24 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0004_auto_20200305_0523'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclassstaff',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, unique=False, null=True),
        ),
        migrations.AddField(
            model_name='facultystaff',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, unique=False, null=True),
        ),
        migrations.AddField(
            model_name='institutionstaff',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, unique=False, null=True),
        ),
        migrations.AddField(
            model_name='issuerstaff',
            name='entity_id',
            field=models.CharField(default=None, max_length=254, unique=False, null=True),
        ),
    ]
