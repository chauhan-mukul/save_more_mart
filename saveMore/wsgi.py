"""
WSGI config for saveMore project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

setting_module='saveMore.deployment_settings' if "RENDER_EXTERNAL_HOSTNAME" in os.environ else 'saveMore.settings' 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting_module)

application = get_wsgi_application()
