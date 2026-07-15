import os

# 1. Permite recibir peticiones desde Docker y la red local
ALLOWED_HOSTS = ['*']

# 2. Agregamos 'telemetria' al final de la lista
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "telemetria",
]

# 3. Reemplazamos SQLite por MySQL para Docker
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('MYSQL_DATABASE', 'ic3_telemetria_db'),
        'USER': os.environ.get('MYSQL_USER', 'berni'),
        'PASSWORD': os.environ.get('MYSQL_PASSWORD', 'password_segura'),
        'HOST': os.environ.get('MYSQL_HOST', 'localhost'),
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}