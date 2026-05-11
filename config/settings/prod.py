import os

from .base import *


SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-oknmc0(#@lvj*e!gkol^uy+c7i!g+q6_1mwuz*)dpjll$_g*ai')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('MYSQL_DATABASE', 'shenzhen_data'),
        'USER': os.getenv('MYSQL_USER', 'xubin'),
        'PASSWORD': os.getenv('MYSQL_PASSWORD', 'Aa@147258'),
        'HOST': os.getenv('MYSQL_HOST', '38.62.168.75'),
        'PORT': os.getenv('MYSQL_PORT', '8899'),
    }
}
