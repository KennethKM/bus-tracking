"""
ASGI config for bus_tracking project.
"""

import os
import django
from django.core.asgi import get_asgi_application

# Set the settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bus_tracking.settings')

# Initialize Django BEFORE importing other stuff
django.setup()

# Now import other modules
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from tracking.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})