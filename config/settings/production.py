from .base import *  # noqa: F401, F403

DEBUG = False

# HTTPS toggle.
# Default False so HTTP-only deployments (bare IP, no TLS reverse proxy)
# don't infinite-redirect or block cookies. Flip to true once a real
# domain + TLS-terminating proxy (Caddy/Nginx) is in front of the app.
FORCE_HTTPS = env.bool("FORCE_HTTPS", default=False)

# Security headers / redirects — all keyed off FORCE_HTTPS
SECURE_SSL_REDIRECT = FORCE_HTTPS
SECURE_HSTS_SECONDS = 31536000 if FORCE_HTTPS else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = FORCE_HTTPS
SECURE_HSTS_PRELOAD = FORCE_HTTPS
SESSION_COOKIE_SECURE = FORCE_HTTPS
CSRF_COOKIE_SECURE = FORCE_HTTPS
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_REDIRECT_EXEMPT = [r"^health/$"]

# CSRF trusted origins — required by Django 4.x+ for any POST whose
# Origin header doesn't match ALLOWED_HOSTS protocol/port. Read from
# env so prod deploys can list the public-facing URL(s) without
# editing this file.
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "gunicorn.error": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
