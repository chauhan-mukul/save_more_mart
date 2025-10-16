import os
import dj_database_url
from .settings import *
from .settings import BASE_DIR

ALLOWED_HOSTS=[os.environ.get('RENDER_EXTERNAL_HOSTNAME')]
CSRF_TRUSTED_ORIGINS=['https://'+os.environ.get('RENDER_EXTERNAL_HOSTNAME')]

DEBUG=False
SECRET_KEY=os.environ.get('SECRET_KEY')

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'corsheaders.middleware.CorsMiddleware',

]
# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
# ]
STORAGES={
    "default":{
        "BACKEND":"django.core.files.storage.FileSystemStorage",
    },
    "staticfiles":{
        "BACKEND":"whitenoise.storage.CompressedStaticFilesStorage",
    },
}
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ['DATABASE_URL'],
        conn_max_age=600
    )
    
}
import os
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError

if os.environ.get('RENDER') == 'true':
    try:
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', '11211')
    except OperationalError:
        pass
