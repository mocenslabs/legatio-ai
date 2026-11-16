"""
ASGI config for Legatio AI project.

Configures Django Channels for WebSocket support.
Source: 02-ARCHITECTURE.md Section 10.1
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.conf import settings
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legatio.settings.development")

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Import WebSocket routing after Django is initialized
from apps.notifications.middleware import JWTAuthMiddleware  # noqa: E402
from apps.notifications.routing import websocket_urlpatterns  # noqa: E402

websocket_stack = JWTAuthMiddleware(URLRouter(websocket_urlpatterns))

# In production, reject WS connections whose Origin does not match ALLOWED_HOSTS.
# Skip in DEBUG so unit/integration WebsocketCommunicator tests (no Origin) still pass.
if not settings.DEBUG:
    websocket_stack = AllowedHostsOriginValidator(websocket_stack)

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": websocket_stack,
    }
)
