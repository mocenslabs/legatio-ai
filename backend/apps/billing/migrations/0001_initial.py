import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Plan",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("code", models.SlugField(max_length=64, unique=True)),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "interval",
                    models.CharField(
                        choices=[
                            ("monthly", "Monthly"),
                            ("yearly", "Yearly"),
                            ("lifetime", "Lifetime"),
                        ],
                        default="monthly",
                        max_length=20,
                    ),
                ),
                (
                    "price_cents",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="List price in cents (display / future billing). 0 = free.",
                    ),
                ),
                ("currency", models.CharField(default="USD", max_length=3)),
                ("limits", models.JSONField(blank=True, default=dict)),
                ("features", models.JSONField(blank=True, default=dict)),
                (
                    "is_public",
                    models.BooleanField(
                        default=True,
                        help_text="If true, plan can be selected by self-serve signup.",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                ("sort_order", models.PositiveSmallIntegerField(default=100)),
                ("external_price_id", models.CharField(blank=True, default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "legatio_billing_plan",
                "ordering": ["sort_order", "price_cents"],
            },
        ),
        migrations.CreateModel(
            name="UsageRecord",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("metric", models.CharField(db_index=True, max_length=64)),
                ("period", models.CharField(db_index=True, help_text="YYYY-MM", max_length=7)),
                ("quantity", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="usage_records",
                        to="organizations.organization",
                    ),
                ),
            ],
            options={
                "db_table": "legatio_billing_usage_record",
            },
        ),
        migrations.CreateModel(
            name="OrganizationSubscription",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("trialing", "Trialing"),
                            ("active", "Active"),
                            ("past_due", "Past due"),
                            ("canceled", "Canceled"),
                            ("incomplete", "Incomplete"),
                        ],
                        db_index=True,
                        default="trialing",
                        max_length=20,
                    ),
                ),
                ("trial_ends_at", models.DateTimeField(blank=True, null=True)),
                ("current_period_start", models.DateTimeField(blank=True, null=True)),
                ("current_period_end", models.DateTimeField(blank=True, null=True)),
                ("cancel_at_period_end", models.BooleanField(default=False)),
                ("external_customer_id", models.CharField(blank=True, default="", max_length=255)),
                (
                    "external_subscription_id",
                    models.CharField(blank=True, default="", max_length=255),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "organization",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subscription",
                        to="organizations.organization",
                    ),
                ),
                (
                    "plan",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="subscriptions",
                        to="billing.plan",
                    ),
                ),
            ],
            options={
                "db_table": "legatio_billing_organization_subscription",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="usagerecord",
            constraint=models.UniqueConstraint(
                fields=("organization", "metric", "period"),
                name="uniq_usage_org_metric_period",
            ),
        ),
    ]
