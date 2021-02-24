from .local import *  # noqa: F403,  F401

LOGGING = ENVIRONMENT_LOGGING

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.file"
