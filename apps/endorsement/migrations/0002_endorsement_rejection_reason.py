# Generated by Django 2.2.26 on 2022-06-01 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('endorsement', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='endorsement',
            name='rejection_reason',
            field=models.CharField(blank=True, default=None, max_length=512, null=True),
        ),
    ]
