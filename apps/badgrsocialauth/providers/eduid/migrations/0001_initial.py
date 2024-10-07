# Generated by Django 3.2.25 on 2024-10-07 11:03

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ValidatedNameAuditTrail',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('action_datetime', models.DateTimeField(auto_now=True)),
                ('user', models.CharField(blank=True, max_length=254)),
                ('old_validated_name', models.CharField(blank=True, max_length=255)),
                ('new_validated_name', models.CharField(blank=True, max_length=255)),
            ],
        ),
    ]
