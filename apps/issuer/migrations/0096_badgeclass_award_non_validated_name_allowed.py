# Generated by Django 2.2.24 on 2021-09-21 11:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0095_auto_20210915_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='award_non_validated_name_allowed',
            field=models.BooleanField(default=False),
        ),
    ]
