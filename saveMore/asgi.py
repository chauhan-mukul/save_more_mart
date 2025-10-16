"""
ASGI config for saveMore project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
setting_module='saveMore.deployment_settings' if "RENDER_EXTERNAL_HOSTNAME" in os.environ else 'saveMore.settings' 
os.environ.setdefault('DJANGO_SETTINGS_MODULE', setting_module)


application = get_asgi_application()
