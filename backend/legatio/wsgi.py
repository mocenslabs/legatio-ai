"""
WSGI config for Legatio AI project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

application = get_wsgi_application()
