from datetime import date, timedelta

# CSV generation
import csv

# File and folder operations
import os

# SMTP library used to send emails.
import smtplib

# Used for creating email message.
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Used for Google Chat Webhook API.
import requests

# Gives Celery access to Flask application config.
from flask import current_app

# Celery object and database.
from app.extensions import celery, db

# Database models.
from app.models import Booking, Trek, User


# HELPER FUNCTIONS
#
# These helper functions are shared by multiple Celery tasks.
#
# They avoid repeating the same code.
#
# =============================================================================


# GOOGLE CHAT WEBHOOK
#
# Sends notification to Google Chat.
#
# Viva:
# Q. What is a webhook?
#
# A:
# A webhook automatically sends data to another application
# whenever an event occurs.
#
def _send_gchat_message(text: str) -> bool:

    # Read webhook URL from config.py
    webhook_url=current_app.config.get(
        "GCHAT_WEBHOOK_URL"
    )

    # Webhook not configured.
    if not webhook_url:

        # During demo,
        # simply print message.
        print(
            "[Webhook not configured]\n",
            text
        )

        return False

    try:

        # POST request to Google Chat.
        resp=requests.post(

            webhook_url,

            json={
                "text":text
            },

            timeout=5

        )

        # Raise exception if failed.
        resp.raise_for_status()

        return True

    except requests.RequestException as e:

        print(

            f"Webhook Failed {e}"

        )

        return False


# EMAIL HELPER
# Sends HTML Email.
#
# Uses SMTP.
#
def _send_email(

to_address,

subject,

html_body

):

    # Read credentials.
    username=current_app.config.get(
        "MAIL_USERNAME"
    )

    password=current_app.config.get(
        "MAIL_PASSWORD"
    )

    # Mail not configured.
    if (

        not username

        or

        not password

        or

        not to_address

    ):

        print(

            html_body

        )

        return False

    try:

        # Create email object.
        msg=MIMEMultipart(

            "alternative"

        )

        msg["Subject"]=subject

        msg["From"]=username

        msg["To"]=to_address

        # Attach HTML.
        msg.attach(

            MIMEText(

                html_body,

                "html"

            )

        )

        # SMTP Server.
        with smtplib.SMTP(

            current_app.config[
                "MAIL_SERVER"
            ],

            current_app.config[
                "MAIL_PORT"
            ]

        ) as server:

            # Enable encryption.
            server.starttls()

            # Login.
            server.login(

                username,

                password

            )

            # Send email.
            server.sendmail(

                username,

                [to_address],

                msg.as_string()

            )

        return True

    except Exception as e:

        print(e)

        return False


# DAILY REMINDER TASK
# Celery Task
#
#
# Runs every day
# at 8:00 AM.
#
# (Configured in extensions.py)
#
@celery.task(
name="app.tasks.daily_reminders"
)

def daily_reminders():

    # Today's date.
    today=date.today()

    # Next 3 days.
    upcoming=today+timedelta(days=3)

    # Find upcoming treks.
    treks=Trek.query.filter(

        Trek.start_date>=today,

        Trek.start_date<=upcoming

    ).all()

    sent_count=0

    # Loop through treks.
    for trek in treks:

        # Find booked users.
        bookings=Booking.query.filter_by(

            trek_id=trek.id,

            status="Booked"

        ).all()

        for booking in bookings:

            user=User.query.get(

                booking.user_id

            )

            if user:

                message=f"""
Reminder

Hi {user.full_name}

Your trek

{trek.trek_name}

starts on

{trek.start_date}
"""

                if _send_gchat_message(

                    message

                ):

                    sent_count+=1

    return f"{sent_count} reminders sent"


# MONTHLY REPORT
#
# Runs
#
# Every Month
#
# 1st Day
#
# 12:05 AM
#
@celery.task(
name="app.tasks.monthly_activity_report"
)

def monthly_activity_report():

    # Count completed treks.
    completed_treks=Trek.query.filter_by(

        status="Completed"

    ).count()

    # Count completed bookings.
    completed_bookings=Booking.query.filter_by(

        status="Completed"

    ).count()

    # Most popular trek.
    popular=(

        db.session.query(

            Trek.trek_name,

            db.func.count(

                Booking.id

            ).label(

                "count"

            )

        )

        .join(

            Booking

        )

        .group_by(

            Trek.id

        )

        .order_by(

            db.func.count(

                Booking.id

            ).desc()

        )

        .first()

    )

    popular_name=(
        popular.trek_name
        if popular
        else
        "None"
    )

    # HTML Email.
    html_body=f"""

<h2>Monthly Report</h2>

Treks Conducted

{completed_treks}

Completed Users

{completed_bookings}

Popular Trek

{popular_name}

"""

    # Find admin email.
    admin=User.query.filter_by(

        role="admin"

    ).first()

    admin_email=(
        admin.email
        if admin
        else None
    )

    # Send email.
    _send_email(

        admin_email,

        "Monthly Report",

        html_body

    )

    return{

        "Treks":completed_treks,

        "Users":completed_bookings,

        "Popular Trek":popular_name

    }


# EXPORT BOOKING HISTORY
#
# User clicks
#
# Export History
#
# Celery creates CSV.
#
@celery.task(
name="app.tasks.export_booking_history"
)

def export_booking_history(user_id):

    # Join Booking and Trek tables.
    bookings=(

        db.session.query(

            Booking,

            Trek

        )

        .join(

            Trek

        )

        .filter(

            Booking.user_id==user_id

        )

        .all()

    )

    # Create exports folder.
    os.makedirs(

        "exports",

        exist_ok=True

    )

    filename=f"exports/user_{user_id}_history.csv"

    with open(

        filename,

        "w",

        newline=""

    ) as file:

        writer=csv.writer(

            file

        )

        # CSV Header.
        writer.writerow([

            "User ID",

            "Trek",

            "Location",

            "Status",

            "Start",

            "End"

        ])

        # CSV Data.
        for booking,trek in bookings:

            writer.writerow([

                user_id,

                trek.trek_name,

                trek.location,

                booking.status,

                trek.start_date,

                trek.end_date

            ])

    print(

        filename

    )

    return filename