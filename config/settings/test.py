from .base import *

SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'test'),
        'USER': os.getenv('MYSQL_USER', ''),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', ''),
        'HOST': os.getenv('MYSQL_HOST', 'host.docker.internal'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
    }
}
