# Generated by Django 3.2.25 on 2024-07-29 11:12

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("directaward", "0016_directaward_grade_achieved"),
    ]

    operations = [
        migrations.CreateModel(
            name="DirectAwardAuditTrail",
            fields=[
                (
                    "pkid",
                    models.BigAutoField(
                        editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                ("login_IP", models.GenericIPAddressField(blank=True, null=True)),
                ("action_datetime", models.DateTimeField(auto_now=True)),
                ("user", models.CharField(blank=True, max_length=254)),
                ("user_agent_info", models.CharField(blank=True, max_length=255)),
                ("action", models.CharField(max_length=40)),
                ("change_summary", models.CharField(blank=True, max_length=199)),
                (
                    "direct_award_entity_id",
                    models.CharField(blank=True, max_length=255),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
