from app.extensions import db
from datetime import datetime


# ==========================================================
# USER
# ==========================================================

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(15))
    role = db.Column(db.String(20), nullable=False)
    # admin / staff / user

    status = db.Column(db.String(20), default="Active")
    # Active / Blacklisted

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    staff_profile = db.relationship(
        "StaffProfile",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan"
    )

    bookings = db.relationship(
        "Booking",
        backref="user",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def get_id(self):
        return str(self.id)


# ==========================================================
# STAFF PROFILE
# ==========================================================

class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    experience = db.Column(db.Integer)

    specialization = db.Column(db.String(100))

    status = db.Column(db.String(20), default="Active")

    treks = db.relationship(
        "Trek",
        backref="staff",
        lazy=True
    )


# ==========================================================
# TREK
# ==========================================================

class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)

    trek_name = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    difficulty = db.Column(db.String(20), nullable=False)
    # Easy / Moderate / Hard

    duration_days = db.Column(db.Integer, nullable=False)

    available_slots = db.Column(db.Integer, nullable=False)

    assigned_staff_id = db.Column(
        db.Integer,
        db.ForeignKey("staff_profiles.id")
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )
    # Pending / Approved / Open / Closed / Completed

    start_date = db.Column(db.Date, nullable=False)

    end_date = db.Column(db.Date, nullable=False)

    description = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    bookings = db.relationship(
        "Booking",
        backref="trek",
        lazy=True,
        cascade="all, delete-orphan"
    )


# ==========================================================
# BOOKING
# ==========================================================

class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    trek_id = db.Column(
        db.Integer,
        db.ForeignKey("treks.id"),
        nullable=False
    )

    booking_date = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    status = db.Column(
        db.String(20),
        default="Booked"
    )
    # Booked / Cancelled / Completed

    payment_status = db.Column(
        db.String(20),
        default="Pending"
    )
    # Pending / Paid / Failed

    __table_args__ = (
        db.UniqueConstraint(
            "user_id",
            "trek_id",
            name="unique_user_trek_booking"
        ),
    )


class Setting(db.Model):
    __tablename__ = "settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Setting {self.key}={self.value}>"



