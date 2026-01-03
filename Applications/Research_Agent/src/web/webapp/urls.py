"""
Django URL configuration for Research Agent API and WebSocket endpoints.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import api_views

# REST API endpoints
api_patterns = [
    # Ingestion endpoints
    path('ingest/start/', api_views.ingest_start, name='ingest_start'),
    path('ingest/status/', api_views.ingest_status, name='ingest_status'),
    
    # Research endpoints
    path('research/query/', api_views.research_query, name='research_query'),
    path('research/<str:id>/', api_views.research_get, name='research_get'),
    
    # Health check
    path('health/', api_views.health_check, name='health_check'),
]

# WebSocket URL patterns (handled by asgi.py routing)
# These will be routed by the ASGI application using channels routing
websocket_patterns = [
    # WebSocket endpoints are handled in asgi.py routing configuration
    # path('ws/ingest/', ws_consumers.IngestionProgressConsumer.as_asgi()),
    # path('ws/research/', ws_consumers.ResearchAnalysisConsumer.as_asgi()),
]

urlpatterns = [
    path('api/', include(api_patterns)),
]
