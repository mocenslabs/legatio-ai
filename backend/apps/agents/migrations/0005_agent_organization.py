# Optional organization scope on Agent

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("agents", "0004_increase_key_prefix_max_length"),
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="agent",
            name="organization",
            field=models.ForeignKey(
                blank=True,
                help_text="Optional organization scope. Null = personal agent owned only by user.",
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="agents",
                to="organizations.organization",
            ),
        ),
        migrations.AddIndex(
            model_name="agent",
            index=models.Index(fields=["organization"], name="idx_agent_organization"),
        ),
    ]
