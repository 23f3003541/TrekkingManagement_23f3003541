from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

import redis

from celery import Celery
from celery.schedules import crontab


# FLASK EXTENSIONS
# Objects are created here but NOT connected to Flask yet.
# They are initialized later inside create_app().
# Viva:
# Q: Why initialize like this?
# To avoid circular imports and to follow Flask's Application Factory Pattern.
#
db = SQLAlchemy()

# Handles JWT authentication.
jwt = JWTManager()

# Enables Cross-Origin Resource Sharing.
cors = CORS()


# REDIS CLIENT
# Raw Redis client used for caching.
#
# Initially None.
# It is assigned inside init_redis().
#
redis_client = None


# CELERY INSTANCE

# Celery handles background tasks.
#
# Example:
# • Send email
# • Monthly report
# • Notifications
#
celery = Celery(__name__)


# INITIALIZE REDIS
# Creates Redis connection using URL from config.py
# redis://localhost:6379/0
#
def init_redis(app):

    global redis_client

    # Connect to Redis.
    redis_client = redis.Redis.from_url(

        app.config["REDIS_URL"],

        # Automatically converts bytes into strings.
        decode_responses=True
    )

    return redis_client


# INITIALIZE CELERY
# Configures Celery Broker, Backend and Scheduled Tasks.
#
def init_celery(app):

    celery.conf.update(

        # Queue where tasks are stored.
        broker_url=app.config["CELERY_BROKER_URL"],

        # Stores completed task results.
        result_backend=app.config["CELERY_RESULT_BACKEND"],

        # Timezone.
        timezone="Asia/Kolkata",

        # Use UTC internally.
        enable_utc=True,

        # Scheduler configuration.
        beat_schedule={

            # DAILY REMINDER
            # Runs every day at .
            #
            "daily-trek-reminders": {

                "task": "app.tasks.daily_reminders",

                "schedule": crontab(
                    hour=20,
                    minute=20
                ),
            },

            # MONTHLY REPORT
            # Runs every month
            # on the 1st day at 12:05 AM.
            #
            "monthly-activity-report": {

                "task": "app.tasks.monthly_activity_report",

                "schedule": crontab(
                    hour=0,
                    minute=5,
                    day_of_month=1
                ),
            },
        },
    )


    # CONTEXT TASK
    # Gives Celery tasks access to Flask's application context.
    # Without this, Celery tasks cannot access:
    # current_app
    # db
    # config cannot be used inside background tasks.
    
    class ContextTask(celery.Task):

        def __call__(self, *args, **kwargs):

            with app.app_context():

                return self.run(*args, **kwargs)


    # Replace default Celery Task.
    celery.Task = ContextTask

    return celery