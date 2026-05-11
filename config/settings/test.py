from .base import *

SECRET_KEY = 'django-insecure-oknmc0(#@lvj*e!gkol^uy+c7i!g+q6_1mwuz*)dpjll$_g*ai'
DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'test'),
        'USER': os.getenv('MYSQL_USER', 'root'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', '123456'),
        'HOST': os.getenv('MYSQL_HOST', 'host.docker.internal'),
        'PORT': os.getenv('MYSQL_PORT', '3306'),
    }
}
