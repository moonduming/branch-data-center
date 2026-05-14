import os
from pathlib import Path
from datetime import timedelta

from celery.schedules import crontab

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'apps.users',
    'apps.organization',
    'apps.datahub',
    'apps.performance',
    'apps.workflow',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'



AUTH_USER_MODEL = 'users.User'


# 默认重置密码/首次登录密码
DEFAULT_RESET_PASSWORD = "123456"


# DRF 全局配置
REST_FRAMEWORK = {
    # 默认认证方式
    # 使用 JWT 认证，DRF 会自动从请求头中解析 token
    # 请求头格式必须是：
    # Authorization: Bearer <access_token>
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # 默认权限控制
    # 所有接口默认都需要登录才能访问
    # 如果某些接口（例如 login、自动登录接口）不需要登录
    # 需要在 view 中单独设置：
    # permission_classes = [AllowAny]
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    # 分页
    "DEFAULT_PAGINATION_CLASS": "common.drf.CountDataPagination",
    "PAGE_SIZE": 10,

    # 统一返回格式
    "DEFAULT_RENDERER_CLASSES": (
        "common.drf.MessageDataJSONRenderer",
    ),
    "EXCEPTION_HANDLER": "common.drf.custom_exception_handler",
}


# JWT 配置
SIMPLE_JWT = {
    # access token 有效期
    # access token 用于访问接口
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    # 不再走 refresh token 续期流程，仅保留兼容配置
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    # 关闭 refresh token 轮换
    'ROTATE_REFRESH_TOKENS': False,
    # 不使用 refresh token 黑名单
    'BLACKLIST_AFTER_ROTATION': False,
    # 登录成功后是否自动更新用户 last_login 字段
    'UPDATE_LAST_LOGIN': False,
    # JWT 签名算法
    # HS256 表示使用 SECRET_KEY 进行 HMAC SHA256 签名
    'ALGORITHM': 'HS256',
    # 请求头类型
    # 前端请求时必须携带：
    # Authorization: Bearer <access_token>
    'AUTH_HEADER_TYPES': ('Bearer',),
    # 使用的 token 类型
    # 这里指定 access token 类型
    'AUTH_TOKEN_CLASSES': (
        'rest_framework_simplejwt.tokens.AccessToken',
    ),
}


# Celery 配置
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', CELERY_BROKER_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = os.getenv('CELERY_TIMEZONE', 'Asia/Shanghai')
CELERY_ENABLE_UTC = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = int(os.getenv('CELERY_TASK_TIME_LIMIT', '28800'))  # 8小时
CELERY_TASK_SOFT_TIME_LIMIT = int(os.getenv('CELERY_TASK_SOFT_TIME_LIMIT', '28200')) # 7小时50分种
HEAD_OFFICE_IMPORT_DAY_OFFSET = int(os.getenv('HEAD_OFFICE_IMPORT_DAY_OFFSET', '1'))
DATAHUB_RESULT_IMPORT_MAX_WORKERS = int(os.getenv('DATAHUB_RESULT_IMPORT_MAX_WORKERS', '4'))
CELERY_BEAT_SCHEDULE = {
    'datahub-run-auto-load-data-backup': {
        'task': 'datahub.run_auto_load_data_backup',
        'schedule': crontab(hour='0', minute='0'),
        'kwargs': {},
    },
    'datahub-run-head-office-import': {
        'task': 'datahub.run_head_office_import',
        'schedule': crontab(minute=os.getenv('HEAD_OFFICE_IMPORT_BEAT_MINUTE', '*/10')),
        'kwargs': {},
    },
    'datahub-run-result-import': {
        'task': 'datahub.run_datahub_result_import',
        'schedule': crontab(minute=os.getenv('DATAHUB_IMPORT_DISPATCH_MINUTE', '*/20')),
        'kwargs': {},
    },
    'datahub-run-post-profit-result-import': {
        'task': 'datahub.run_datahub_post_profit_result_import',
        'schedule': crontab(
            hour=os.getenv('DATAHUB_POST_PROFIT_IMPORT_DISPATCH_HOUR', '0'),
            minute=os.getenv('DATAHUB_POST_PROFIT_IMPORT_DISPATCH_MINUTE', '30'),
        ),
        'kwargs': {},
    },
}


# DataHub 指标计算配置
DATAHUB_SQL_EXECUTION_ENABLED = os.getenv('DATAHUB_SQL_EXECUTION_ENABLED', 'false').lower() == 'true'
DATAHUB_DEFAULT_DAY_COUNT = int(os.getenv('DATAHUB_DEFAULT_DAY_COUNT', '1'))

# 总行导入定时任务开关
HEAD_OFFICE_IMPORT_BEAT_ENABLED = os.getenv('HEAD_OFFICE_IMPORT_BEAT_ENABLED', 'false').lower() == 'true'


# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization

LANGUAGE_CODE = 'zh-hans'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True
USE_TZ = True


# Static files

STATIC_URL = 'static/'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# 日志目录
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)


# todo: 日志配置需要优化
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(name)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s'
        },
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },

        'django_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'django.log'),
            'when': 'D',
            'interval': 7,
            'backupCount': 4,
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
        'celery_file': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'celery.log'),
            'when': 'D',
            'interval': 3,
            'backupCount': 10,
            'encoding': 'utf-8',
            'formatter': 'verbose',
        },
    },

    'root': {
        'handlers': ['console', 'django_file'],
        'level': 'INFO',
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },

        'django.request': {
            'handlers': ['console', 'django_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.datahub': {
            'handlers': ['console', 'django_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'celery_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
