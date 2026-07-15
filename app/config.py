import os

# BASE DIRECTORY
# __file__ → Current file (config.py)
#
# dirname(__file__)          -> app/
# dirname(dirname(__file__)) -> Project Root
#
# Example:
#
# TrekManagement/
# ├── app/
# │   ├── config.py
# │   ├── models.py
# │
# ├── tma.db
#
# BASE_DIR points to TrekManagement/
#
BASE_DIR = os.path.abspath(
    os.path.dirname(
        os.path.dirname(__file__)
    )
)


# CONFIGURATION CLASS
# Stores all application configuration in one place.
#
# Viva:
# Q: Why create a Config class?
#
# A:
# It keeps all project settings centralized, making them easy to manage,
# update, and reuse throughout the application.
#
class Config:

    # Flask Secret Key
    # Used for:
    # - Session security
    # - Signing cookies
    # - Preventing data tampering
    
    # os.environ.get() first checks environment variables.
    # If not found, it uses the default value.
    
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-change-me"
    )


    # Database Configuration
    # If DATABASE_URL exists:
    #     Use it.
    #
    # Otherwise:
    #     Use SQLite database.
    #
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'tma.db')}"
    )


    # Disables unnecessary tracking to improve performance.
    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # JWT Configuration
        # Secret key used to sign JWT tokens.
    #
    JWT_SECRET_KEY = os.environ.get(
        "JWT_SECRET_KEY",
        "dev-jwt-secret-change-me"
    )

    # JWT token validity period.
    #
    # 60 seconds × 60 minutes × 8 hours
    #
    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8


    # Redis Configuration
    # Redis database 0
    #
    REDIS_URL = os.environ.get(
        "REDIS_URL",
        "redis://localhost:6379/0"
    )


    # Celery Configuration
    # Broker:
    # Stores task queue.
    #
    CELERY_BROKER_URL = os.environ.get(
        "CELERY_BROKER_URL",
        "redis://localhost:6379/1"
    )

    # Stores completed task results.
    #
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND",
        "redis://localhost:6379/2"
    )


    # Cache Expiry
    # Trek data remains cached for 60 seconds.
    #
    TREK_CACHE_TTL = 60


    # Email Configuration
    # SMTP server settings.

    #webhooks
    #
    MAIL_SERVER = os.environ.get(
        "MAIL_SERVER",
        "smtp.gmail.com"
    )

    MAIL_PORT = int(
        os.environ.get(
            "MAIL_PORT",
            587
        )
    )

    MAIL_USERNAME = os.environ.get(
        "23bec035@sot.pdpu.ac.in",
        ""
    )

    MAIL_PASSWORD = os.environ.get(
        "Shubhang0!81#",
        ""
    )


    # -------------------------------------------------------------------------
    # Google Chat Webhook
    # -------------------------------------------------------------------------
    #
    # Used for sending automated notifications to Google Chat.
    #
    GCHAT_WEBHOOK_URL = os.environ.get(
        "https://chat.googleapis.com/v1/spaces/AAQAtXEyTWY/messages?key=AIzaSyDdI0hCZtE6vySjMm-WEfRq3CPzqKqqsHI&token=2U8b79vc3wEsULq13CSgMtyoNgQ5yZ_ZciQzNwgRBA4",
        ""
    )