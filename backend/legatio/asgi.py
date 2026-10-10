"""
ASGI config for Legatio AI project.

Configures Django Channels for WebSocket support.
Source: 02-ARCHITECTURE.md Section 10.1
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddleware(URLRouter(websocket_urlpatterns)),
    }
)
