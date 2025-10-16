from django.apps import AppConfig
import os

class YourAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'your_app'

    def ready(self):
        if os.environ.get('RENDER') == 'true':
            # Import here, not at module level
            from django.contrib.auth import get_user_model
            from django.db.utils import OperationalError, ProgrammingError
            
            try:
                User = get_user_model()
                if not User.objects.filter(username='admin').exists():
                    User.objects.create_superuser('admin', 'admin@example.com', '11211')
            except (OperationalError, ProgrammingError):
                # Database tables might not exist yet
                pass
