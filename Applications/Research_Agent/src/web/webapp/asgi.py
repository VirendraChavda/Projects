"""
ASGI config for Research Agent - handles both HTTP and WebSocket protocols.
"""
import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')
django.setup()

from webapp import ws_consumers
from django.urls import path

# HTTP routes
django_asgi_app = get_asgi_application()

# WebSocket routes
websocket_urlpatterns = [
    path('ws/ingest/', ws_consumers.IngestionProgressConsumer.as_asgi()),
    path('ws/research/', ws_consumers.ResearchAnalysisConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
