# Generated manually for totp_secret encryption (Fernet tokens need more space)

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="totp_secret",
            field=models.CharField(
                blank=True,
                help_text="Fernet-encrypted TOTP secret for 2FA (at-rest encryption).",
                max_length=255,
                null=True,
            ),
        ),
    ]
