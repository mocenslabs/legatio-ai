"""Seed default billing plans."""

from django.core.management.base import BaseCommand

from apps.billing.services import ensure_default_plans


class Command(BaseCommand):
    help = "Create or update default Free / Pro / Business plans"

    def handle(self, *args, **options):  # type: ignore[no-untyped-def]
        created = ensure_default_plans()
        self.stdout.write(self.style.SUCCESS(f"Plans ready. Newly created: {len(created)}"))
