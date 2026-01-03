"""
WSGI config for Research Agent - for traditional deployment.
"""
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webapp.settings')

application = get_wsgi_application()
