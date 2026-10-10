#!/usr/bin/env python
"""
Compatibility entrypoint for DEL-036 path: backend/scripts/seed_data.py

Canonical implementation:
    python manage.py seed_mvp [--force]

Prefer from repo root:
    ./scripts/seed.sh
    ./scripts/seed.sh --force
"""

from __future__ import annotations

import os
import sys


def main() -> int:
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_root not in sys.path:
        sys.path.insert(0, backend_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

    import django

    django.setup()

    from django.core.management import call_command

    force = "--force" in sys.argv or "-f" in sys.argv
    call_command("seed_mvp", force=force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
