SECRET_KEY = 'pasmo'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ASGI_APPLICATION = 'tests.routing.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

MIDDLEWARE_CLASSES = []

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'channels',
    'tests.apps.TestsConfig',
)
