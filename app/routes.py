from datetime import datetime

# Flask utilities
# request  -> Reads incoming HTTP request data
# jsonify  -> Converts Python objects into JSON response
# abort    -> Stops execution and returns an HTTP error
from flask import request, jsonify, abort


# Therefore every incoming date must be converted before storing it.
#  function 
# SQLAlchemy Date columns cannot directly store strings.
# They require Python date objects.
def _parse_date(value):

    # If no date is supplied
    if value in (None, ""):
        return None

    # If already a date object
    # return without converting.
    if hasattr(value, "isoformat") and not isinstance(value, str):
        return value

    # Convert string into Python date object.
    return datetime.strptime(value, "%Y-%m-%d").date()


# current_app = currently running Flask application.
# Q: Why current_app instead of Flask()?
# The Flask application has already been created inside create_app().
# current_app simply refers to that existing application.
from flask import current_app as app


# Database object
from app.extensions import db

from app.models import (
    Booking,
    Setting,
    StaffProfile,
    Trek,
    User
)

# Authentication helper functions.

# role_required()=Restricts API access according to role.
# get_current_user() = Returns the currently logged-in user.
from app.auth import (
    role_required,
    get_current_user
)

# Redis cache functions.
# cache_delete_prefix() = Removes outdated cached data.
# cached_treks_response() = Automatically caches trek list responses.
from app.cache import (
    cache_delete_prefix,
    cached_treks_response
)


# TREK ROUTES
# These APIs are shared between
# Admin
# Staff
# User


# SERIALIZE TREK =  SQLAlchemy model objects cannot be returned directly as JSON.
# This function converts a Trek object into a dictionary.
#
# Database Object
#       ↓
# Dictionary
#       ↓
# JSON Response
#
# Viva:
# Why serialize objects?
# jsonify() can convert dictionaries into JSON,
# but it cannot directly convert SQLAlchemy model objects.
#
def _serialize_trek(trek):

    return {

        "id": trek.id,

        "trek_name": trek.trek_name,

        "location": trek.location,

        "difficulty": trek.difficulty,

        "duration_days": trek.duration_days,

        "available_slots": trek.available_slots,

        "assigned_staff_id": trek.assigned_staff_id,

        "status": trek.status,

        "start_date": trek.start_date,

        "end_date": trek.end_date,
    }


# LIST ALL TREKS

# GET /api/treks

# Supports:
#
# • Search
# • Filter
# • Pagination
# • Redis Cache

@app.route("/api/treks", methods=["GET"])

# Before executing this function,
# Redis cache is checked.
#
# Cache Hit
# Return cached data
# Cache Miss
# Query database
@cached_treks_response
def trek_list():

    # Search keyword.
    q = request.args.get("q", "").strip()

    # Difficulty filter.
    # Easy
    # Medium
    # Hard
    difficulty = request.args.get("difficulty")

    # Location filter.
    # Example:
    # Manali
    # Ladakh
    location = request.args.get("location")

    # By default,
    # only open treks are displayed.
    status = request.args.get("status", "Open")

    # Pagination
    page = int(request.args.get("page", 1))

    # Number of treks displayed per page.
    #
    per_page = int(request.args.get("per_page", 9))

    # Initial query.
    # SELECT * FROM Trek;
    query = Trek.query

    # Filter by status.
    if status:
        query = query.filter(
            Trek.status == status
        )

    # Filter by difficulty.
    if difficulty:
        query = query.filter(
            Trek.difficulty == difficulty
        )

    # Filter by location.
    #
    # ilike()
    #
    # Case-insensitive.
    #
    if location:
        query = query.filter(
            Trek.location.ilike(
                f"%{location}%"
            )
        )

    # Search trek name OR location.
    #
    # Equivalent SQL: WHERE trek_name LIKE ... OR location LIKE ...
    if q:

        query = query.filter(

            db.or_(

                Trek.trek_name.ilike(f"%{q}%"),

                Trek.location.ilike(f"%{q}%")
            )
        )

    # Pagination.
    
    # Instead of loading all treks,
    # only one page is returned.
    
    paginated = query.paginate(

        page=page,

        per_page=per_page,

        error_out=False
    )

    # JSON response.
    return {

        "treks": [

            _serialize_trek(t)

            for t in paginated.items
        ],

        "total": paginated.total,

        "page": page,

        "pages": paginated.pages,
    }


# SINGLE TREK DETAILS
# GET /api/treks/<trek_id>
#
# Example:
#
# /api/treks/5
#
@app.route("/api/treks/<int:trek_id>", methods=["GET"])
def trek_get(trek_id):

    # Searches trek by primary key.

    # If trek exists:
    # Returns Trek object.
    # Otherwise:
    # Automatically returns
    # 404 Not Found.
    trek = Trek.query.get_or_404(trek_id)

    # Convert Trek object into JSON.
    return jsonify(
        _serialize_trek(trek)
    )


# ADMIN ROUTES
# These APIs are accessible ONLY by Admin.
# Every API is protected using:
# @role_required("admin")
# This means:
# 1. JWT Token must be valid.
# 2. User must be logged in.
# 3. User role must be "admin".
# 4. User account must not be blacklisted.
# If any check fails:
# 401 Unauthorized
# OR
# 403 Forbidden


# =============================================================================
# ADMIN DASHBOARD
# =============================================================================
#
# GET /api/admin/dashboard
#
# Returns overall system statistics.
#
@app.route("/api/admin/dashboard", methods=["GET"])

# Only Admin can access.
@role_required("admin")

def admin_dashboard():

    return jsonify({

        # Total number of treks.
        "total_treks": Trek.query.count(),

        # Count only normal users.
        "total_users": User.query.filter_by(
            role="user"
        ).count(),

        # Count staff members.
        "total_staff": User.query.filter_by(
            role="staff"
        ).count(),

        # Total bookings.
        "total_bookings": Booking.query.count(),
    })


# CREATE TREK
# POST /api/admin/treks
#
# Admin creates a new trek.
#
@app.route("/api/admin/treks", methods=["POST"])
@role_required("admin")

def admin_create_trek():

    # Read JSON body.
    data = request.get_json()

    # Create Trek object.
    trek = Trek(

        trek_name=data["trek_name"],

        location=data["location"],

        difficulty=data["difficulty"],

        duration_days=data["duration_days"],

        available_slots=data["available_slots"],

        # Optional staff assignment.
        assigned_staff_id=data.get(
            "assigned_staff_id"
        ),

        # Default status.
        # Newly created treks must be visible to users immediately.
        status=data.get(
            "status",
            "Open"
        ),

        # Convert string into date object.
        start_date=_parse_date(
            data.get("start_date")
        ),

        end_date=_parse_date(
            data.get("end_date")
        ),
    )

    # Add object into session.
    db.session.add(trek)

    # Permanently save.
    db.session.commit()

    # Trek list cache becomes outdated.
    cache_delete_prefix("treks")

    return jsonify({

        "message": "Trek created",

        "id": trek.id

    }), 201


# UPDATE TREK
# PUT /api/admin/treks/<trek_id>
#
# Updates an existing trek.
#
@app.route("/api/admin/treks/<int:trek_id>", methods=["PUT"])
@role_required("admin")

def admin_update_trek(trek_id):

    # Find trek.
    #
    # If not found
    #
    # Automatically returns 404.
    #
    trek = Trek.query.get_or_404(
        trek_id
    )

    data = request.get_json()

    # Update fields dynamically.
    #
    # setattr(object, field, value)
    #
    # Works like:
    #
    # trek.location="Manali"
    #
    for field in (

        "trek_name",

        "location",

        "difficulty",

        "duration_days",

        "available_slots",

        "assigned_staff_id",

        "status"

    ):

        if field in data:

            setattr(

                trek,

                field,

                data[field]

            )

    # Update dates.
    if "start_date" in data:

        trek.start_date = _parse_date(

            data["start_date"]

        )

    if "end_date" in data:

        trek.end_date = _parse_date(

            data["end_date"]

        )

    db.session.commit()

    # Refresh Redis cache.
    cache_delete_prefix("treks")

    return jsonify({

        "message": "Trek updated"

    })


# DELETE TREK
# DELETE /api/admin/treks/<id>
#
# Removes trek permanently.
#
@app.route("/api/admin/treks/<int:trek_id>", methods=["DELETE"])
@role_required("admin")

def admin_delete_trek(trek_id):

    trek = Trek.query.get_or_404(
        trek_id
    )

    db.session.delete(trek)

    db.session.commit()

    # Remove cached trek list.
    cache_delete_prefix("treks")

    return jsonify({

        "message": "Trek removed"

    })


# CREATE STAFF
# POST /api/admin/staff

# Staff members CANNOT register themselves.

# Admin creates them.

@app.route("/api/admin/staff", methods=["POST"])
@role_required("admin")

def admin_create_staff():

    data = request.get_json()

    # Import helper.
    from app.auth import create_staff_account

    try:

        user = create_staff_account(

            full_name=data["full_name"],

            email=data["email"],

            password=data["password"],

            contact_number=data.get(
                "contact_number"
            ),

            experience=data.get(
                "experience"
            ),

            specialization=data.get(
                "specialization"
            ),

        )

    except ValueError as e:

        return jsonify({

            "message": str(e)

        }),409

    return jsonify({

        "message":"Staff created",

        "user_id":user.id,

        "staff_profile_id":user.staff_profile.id,

    }),201


# LIST STAFF
# GET /api/admin/staff
# Search and display staff members.
#
@app.route("/api/admin/staff", methods=["GET"])
@role_required("admin")

def admin_list_staff():

    # Search keyword.
    q=request.args.get("q","").strip()

    # Only staff accounts.
    query=User.query.filter_by(

        role="staff"

    )

    # Search by name or email.
    if q:

        query=query.filter(

            db.or_(

                User.full_name.ilike(f"%{q}%"),

                User.email.ilike(f"%{q}%")

            )
        )

    staff=query.all()

    return jsonify([{

        "id":s.id,

        # Used for assigning trek.
        "staff_profile_id":
        s.staff_profile.id
        if s.staff_profile
        else None,

        "full_name":s.full_name,

        "email":s.email,

        "contact_number":s.contact_number,

        "status":s.status,

    } for s in staff])


# ASSIGN STAFF TO TREK
# POST
# /api/admin/staff/<staff_profile_id>/assign/<trek_id>
# Admin assigns one staff member to one trek.
#
@app.route(
"/api/admin/staff/<int:staff_profile_id>/assign/<int:trek_id>",
methods=["POST"]
)

@role_required("admin")

def admin_assign_staff(

staff_profile_id,

trek_id

):

    trek=Trek.query.get_or_404(

        trek_id

    )

    # Verify staff exists.
    StaffProfile.query.get_or_404(

        staff_profile_id

    )

    # Assign staff.
    trek.assigned_staff_id=staff_profile_id

    db.session.commit()

    cache_delete_prefix("treks")

    return jsonify({

        "message":"Staff assigned"

    })


# BLACKLIST STAFF
# PATCH

# Changes status:
# Active
# Blacklisted
@app.route(
"/api/admin/staff/<int:staff_id>/status",
methods=["PATCH"]
)

@role_required("admin")

def admin_toggle_staff_status(

staff_id

):

    staff=User.query.get_or_404(

        staff_id

    )

    data=request.get_json()

    staff.status=data["status"]

    db.session.commit()

    return jsonify({

        "message":f"Staff status set to {staff.status}"

    })


# LIST USERS
# Returns all Trek Users.
#
@app.route("/api/admin/users",methods=["GET"])
@role_required("admin")

def admin_list_users():

    q=request.args.get("q","").strip()

    query=User.query.filter_by(

        role="user"

    )

    if q:

        query=query.filter(

            db.or_(

                User.full_name.ilike(

                    f"%{q}%"

                ),

                User.email.ilike(

                    f"%{q}%"

                )

            )
        )

    users=query.all()

    return jsonify([{

        "id":u.id,

        "full_name":u.full_name,

        "email":u.email,

        "contact_number":u.contact_number,

        "status":u.status,

    } for u in users])


# BLACKLIST USER
# PATCH
# Admin changes
# Active or  Blacklisted

@app.route(
"/api/admin/users/<int:user_id>/status",
methods=["PATCH"]
)

@role_required("admin")

def admin_toggle_user_status(

user_id

):

    user=User.query.get_or_404(

        user_id

    )

    data=request.get_json()

    user.status=data["status"]

    db.session.commit()

    return jsonify({

        "message":f"User status set to {user.status}"

    })


# VIEW BOOKINGS
# GET /api/admin/bookings
# Returns every booking.

@app.route("/api/admin/bookings",methods=["GET"])
@role_required("admin")

def admin_all_bookings():

    bookings=Booking.query.order_by(

        Booking.booking_date.desc()

    ).all()

    return jsonify([{

        "id":b.id,

        "user_id":b.user_id,

        "user_name":
        b.user.full_name
        if b.user
        else None,

        "trek_id":b.trek_id,

        "trek_name":
        b.trek.trek_name
        if b.trek
        else None,

        "booking_date":b.booking_date,

        "status":b.status,

    } for b in bookings])



# STAFF ROUTES
# These APIs can only be accessed by Staff.
# Every API is protected using:
# @role_required("staff")

# Authentication Checks:

# 1. Valid JWT Token
# 2. User Role = Staff
# 3. Account must not be Blacklisted

##
# VERIFY STAFF OWNS TREK

# This helper ensures that a staff member can manage
# ONLY the trek assigned to them.

# Example:
# Staff A -> Trek 1  Staff A cannot modify Trek 2.

def _assert_owns_trek(trek, user):

    # Get logged-in staff profile.
    profile = user.staff_profile

    # If no profile exists
    # OR
    # Staff is not assigned to this trek
    #
    # Return 403 Forbidden.
    if profile is None or trek.assigned_staff_id != profile.id:

        abort(
            403,
            description="You are not assigned to this trek"
        )


# STAFF DASHBOARD
# GET /api/staff/dashboard

# Shows dashboard statistics.
@app.route("/api/staff/dashboard", methods=["GET"])
@role_required("staff")

def staff_dashboard():

    # Get logged-in user.
    user = get_current_user()

    # Get StaffProfile ID.
    profile_id = (
        user.staff_profile.id
        if user.staff_profile
        else None
    )

    # Fetch treks assigned to this staff.
    treks = Trek.query.filter_by(
        assigned_staff_id=profile_id
    ).all() if profile_id else []

    # Count booked participants.
    total_participants = sum(

        Booking.query.filter_by(

            trek_id=t.id,

            status="Booked"

        ).count()

        for t in treks
    )

    # Count ongoing treks.
    ongoing = sum(

        1

        for t in treks

        if t.status == "Open"

    )

    return jsonify({

        "assigned_treks": len(treks),

        "total_participants": total_participants,

        "ongoing_treks": ongoing,

    })


# STAFF VIEW ASSIGNED TREKS
# GET /api/staff/treks
# Shows only treks assigned
# to currently logged-in staff.
#
@app.route("/api/staff/treks", methods=["GET"])
@role_required("staff")

def staff_my_treks():

    user = get_current_user()

    profile_id = (
        user.staff_profile.id
        if user.staff_profile
        else None
    )

    treks = Trek.query.filter_by(

        assigned_staff_id=profile_id

    ).all() if profile_id else []

    return jsonify([{

        "id": t.id,

        "trek_name": t.trek_name,

        "location": t.location,

        "duration_days": t.duration_days,

        "available_slots": t.available_slots,

        "status": t.status,

        "start_date": t.start_date,

        "end_date": t.end_date,

        # Number of confirmed bookings.
        "booked_count":

        Booking.query.filter_by(

            trek_id=t.id,

            status="Booked"

        ).count(),

    } for t in treks])


# UPDATE TREK
# PATCH /api/staff/treks/<trek_id>
#
# Staff can update:
#
# • Available Slots
# • Trek Status
#
# Staff CANNOT update
# another staff's trek.
#
@app.route("/api/staff/treks/<int:trek_id>", methods=["PATCH"])
@role_required("staff")

def staff_update_trek(trek_id):

    user = get_current_user()

    trek = Trek.query.get_or_404(
        trek_id
    )

    # Verify ownership.
    _assert_owns_trek(
        trek,
        user
    )

    data = request.get_json()

    # Update slots.
    if "available_slots" in data:

        trek.available_slots = data[
            "available_slots"
        ]

    # Update trek status.
    if "status" in data:

        trek.status = data[
            "status"
        ]

    db.session.commit()

    # Refresh Redis cache.
    cache_delete_prefix("treks")

    return jsonify({

        "message": "Trek updated"

    })


# STAFF PROFILE
# GET
# Returns profile details.
#
# PUT
# Updates profile.
#
@app.route("/api/staff/profile", methods=["GET", "PUT"])
@role_required("staff")

def staff_profile():

    user = get_current_user()

    profile = user.staff_profile

    # -----------------------
    # VIEW PROFILE
    # -----------------------
    if request.method == "GET":

        return jsonify({

            "full_name": user.full_name,

            "email": user.email,

            "contact_number": user.contact_number,

            "status": user.status,

            "experience":
            profile.experience
            if profile
            else None,

            "specialization":
            profile.specialization
            if profile
            else None,

        })

    # -----------------------
    # UPDATE PROFILE
    # -----------------------

    data = request.get_json() or {}

    # Update common fields.
    if "full_name" in data:

        user.full_name = data["full_name"]

    if "contact_number" in data:

        user.contact_number = data[
            "contact_number"
        ]

    # Update staff profile.
    if profile:

        if "experience" in data:

            profile.experience = data[
                "experience"
            ]

        if "specialization" in data:

            profile.specialization = data[
                "specialization"
            ]

    db.session.commit()

    return jsonify({

        "message": "Profile updated"

    })


# MARK TREK COMPLETED
 # POST
#
# /api/staff/treks/<trek_id>/complete
#
# Marks trek completed.
#
# Also updates every booking
# from Booked
# to Completed.
#
@app.route(
"/api/staff/treks/<int:trek_id>/complete",
methods=["POST"]
)

@role_required("staff")

def staff_mark_completed(trek_id):

    user = get_current_user()

    trek = Trek.query.get_or_404(
        trek_id
    )

    _assert_owns_trek(
        trek,
        user
    )

    # Update trek.
    trek.status = "Completed"

    db.session.commit()

    # Update bookings.
    Booking.query.filter_by(

        trek_id=trek.id,

        status="Booked"

    ).update({

        "status": "Completed"

    })

    db.session.commit()

    cache_delete_prefix("treks")

    return jsonify({

        "message":
        "Trek marked as completed"

    })


# MARK TREK STARTED
# POST

# /api/staff/treks/<trek_id>/start

# Changes status to Open.

@app.route(
"/api/staff/treks/<int:trek_id>/start",
methods=["POST"]
)

@role_required("staff")

def staff_mark_started(trek_id):

    user = get_current_user()

    trek = Trek.query.get_or_404(
        trek_id
    )

    _assert_owns_trek(
        trek,
        user
    )

    trek.status = "Open"

    db.session.commit()

    cache_delete_prefix("treks")

    return jsonify({

        "message":
        "Trek marked as started"

    })


# VIEW PARTICIPANTS
#
# GET
#
# /api/staff/treks/<trek_id>/participants
#
# Displays participants
# of assigned trek.
#
@app.route(
"/api/staff/treks/<int:trek_id>/participants",
methods=["GET"]
)

@role_required("staff")

def staff_participants(trek_id):

    user = get_current_user()

    trek = Trek.query.get_or_404(
        trek_id
    )

    # Verify trek ownership.
    _assert_owns_trek(
        trek,
        user
    )

    bookings = Booking.query.filter_by(

        trek_id=trek.id

    ).all()

    return jsonify([{

        "booking_id": b.id,

        "user_id": b.user_id,

        "booking_date": b.booking_date,

        "status": b.status,

    } for b in bookings])


# =============================================================================
# USER (TREKKER) ROUTES
# =============================================================================
#
# These APIs are accessible ONLY by normal users (Trekkers).
#
# Every API is protected using:
#
# @role_required("user")
#
# Checks:
# 1. Valid JWT Token
# 2. Logged in user
# 3. User role = user
# 4. Account not blacklisted
#
# =============================================================================


# =============================================================================
# USER DASHBOARD
# =============================================================================
#
# GET /api/user/dashboard
#
# Displays all bookings made by the currently logged-in user.
#
@app.route("/api/user/dashboard", methods=["GET"])
@role_required("user")
def user_dashboard():

    # Get currently logged-in user.
    user = get_current_user()

    # Fetch all bookings of this user.
    bookings = Booking.query.filter_by(
        user_id=user.id
    ).all()

    # Return booking details.
    return jsonify({

        "my_bookings":[{

            "booking_id":b.id,

            "trek_id":b.trek_id,

            # Trek name
            "trek_name":
            b.trek.trek_name
            if b.trek
            else "",

            # Trek duration.
            "trek_dates":

            (
                f"{b.trek.start_date} - {b.trek.end_date}"

                if b.trek

                else ""

            ),

            "booking_date":b.booking_date,

            "status":b.status,

        } for b in bookings]

    })


# =============================================================================
# USER PROFILE

# GET
# Returns user profile.
#
# PUT
# Updates profile.
#
@app.route("/api/user/profile", methods=["GET","PUT"])
@role_required("user")

def user_profile():

    user=get_current_user()

    # --------------------------
    # VIEW PROFILE
    # --------------------------
    if request.method=="GET":

        return jsonify({

            "id":user.id,

            "full_name":user.full_name,

            "email":user.email,

            "contact_number":user.contact_number,

        })

    # --------------------------
    # UPDATE PROFILE
    # --------------------------

    data=request.get_json()

    # Update selected fields.
    for field in (

        "full_name",

        "contact_number"

    ):

        if field in data:

            setattr(

                user,

                field,

                data[field]

            )

    db.session.commit()

    return jsonify({

        "message":"Profile updated"

    })


# BOOK TREK

# POST /api/user/bookings
#
# User books a trek.
#
# Validation:
#
# • Trek must be Open.
# • Slots must be available.
# • User cannot book same trek twice.
#
@app.route("/api/user/bookings", methods=["POST"])
@role_required("user")

def user_book_trek():

    user=get_current_user()

    data=request.get_json()

    trek_id=data["trek_id"]

    # Find trek.
    trek=Trek.query.get_or_404(

        trek_id

    )

    # Trek closed.
    if trek.status!="Open":

        return jsonify({

            "error":
            "This trek is not open for booking"

        }),400

    # No slots.
    if trek.available_slots<=0:

        return jsonify({

            "error":
            "No slots available"

        }),400

    # Prevent duplicate booking.
    existing=Booking.query.filter_by(

        user_id=user.id,

        trek_id=trek_id,

        status="Booked"

    ).first()

    if existing:

        return jsonify({

            "error":
            "You already have an active booking"

        }),400

    # Create booking.
    booking=Booking(

        user_id=user.id,

        trek_id=trek_id,

        booking_date=datetime.utcnow(),

        status="Booked"

    )

    # Reduce slot count.
    trek.available_slots-=1

    db.session.add(

        booking

    )

    db.session.commit()

    # Remove outdated cache.
    cache_delete_prefix(

        "treks"

    )

    return jsonify({

        "message":"Trek booked",

        "booking_id":booking.id

    }),201


# CANCEL BOOKING
# POST
#
# /api/user/bookings/<booking_id>/cancel
#
# User cancels booking.
#
@app.route(
"/api/user/bookings/<int:booking_id>/cancel",
methods=["POST"]
)

@role_required("user")

def user_cancel_booking(

booking_id

):

    user=get_current_user()

    booking=Booking.query.get_or_404(

        booking_id

    )

    # Ensure booking belongs
    # to logged-in user.
    if booking.user_id!=user.id:

        return jsonify({

            "error":
            "Not your booking"

        }),403

    # Only active bookings.
    if booking.status!="Booked":

        return jsonify({

            "error":
            "Only active bookings can be cancelled"

        }),400

    # Cancel booking.
    booking.status="Cancelled"

    trek=Trek.query.get(

        booking.trek_id

    )

    # Increase available slots.
    if trek:

        trek.available_slots+=1

    db.session.commit()

    cache_delete_prefix(

        "treks"

    )

    return jsonify({

        "message":
        "Booking cancelled"

    })


# USER HISTORY
# GET /api/user/history
#
# Shows:
#
# Completed
#
# Cancelled
#
# Bookings.
#
@app.route("/api/user/history", methods=["GET"])
@role_required("user")

def user_history():

    user=get_current_user()

    bookings=Booking.query.filter_by(

        user_id=user.id

    ).filter(

        Booking.status.in_(

            [

                "Completed",

                "Cancelled"

            ]

        )

    ).all()

    return jsonify([{

        "trek_id":b.trek_id,

        "trek_name":
        b.trek.trek_name
        if b.trek
        else "",

        "trek_dates":
        f"{b.trek.start_date} - {b.trek.end_date}"
        if b.trek
        else "",

        "completed_on":

        b.trek.end_date.isoformat()

        if b.status=="Completed"

        and b.trek

        else None,

        "status":b.status,

    } for b in bookings])


# ADMIN SETTINGS
#
# GET
#
# Returns application settings.
#
# PUT
#
# Updates settings.
#
@app.route("/api/admin/settings", methods=["GET","PUT"])
@role_required("admin")

def admin_settings():

    # View settings.
    if request.method=="GET":

        settings=Setting.query.all()

        payload={

            s.key:s.value

            for s in settings

        }

        # Default values.
        payload.setdefault(

            "site_name",

            "Trekking MA"

        )

        payload.setdefault(

            "support_email",

            "support@example.com"

        )

        payload.setdefault(

            "maintenance_message",

            ""

        )

        return jsonify(payload)

    # Update settings.
    data=request.get_json() or {}

    allowed=[

        "site_name",

        "support_email",

        "maintenance_message"

    ]

    for key in allowed:

        if key in data:

            setting=Setting.query.filter_by(

                key=key

            ).first()

            if setting:

                setting.value=str(

                    data[key]

                )

            else:

                setting=Setting(

                    key=key,

                    value=str(data[key])

                )

                db.session.add(setting)

    db.session.commit()

    return jsonify({

        "message":
        "Settings updated"

    })


# EXPORT BOOKING HISTORY
#
# POST
#
# Starts background CSV export.
#
# Celery executes this task.
#
@app.route("/api/user/export-history", methods=["POST"])
@role_required("user")

def user_export_history():

    user=get_current_user()

    from app.tasks import export_booking_history

    # delay()
    # sends task to Celery Worker.
    task=export_booking_history.delay(

        user.id

    )

    return jsonify({

        "message":"Export started",

        "task_id":task.id

    }),202


# EXPORT STATUS
# GET
#
# Checks whether CSV export
# has finished.
#
@app.route(
"/api/user/export-history/status/<task_id>",
methods=["GET"]
)

@role_required("user")

def user_export_status(task_id):

    from app.extensions import celery

    # Get task status.
    result=celery.AsyncResult(

        task_id

    )

    payload={

        "state":result.state

    }

    if result.state=="SUCCESS":

        filename=result.result.split("/")[-1]

        payload["filename"]=filename

        payload["download_url"]=\
        f"/api/user/export-history/download/{filename}"

    elif result.state=="FAILURE":

        payload["error"]=str(

            result.result

        )

    return jsonify(payload)


# DOWNLOAD CSV


# Only owner can download.
#
@app.route(
"/api/user/export-history/download/<filename>",
methods=["GET"]
)

@role_required("user")

def user_export_download(filename):

    from flask import send_from_directory

    user=get_current_user()

    # Prevent downloading another user's file.
    if not filename.startswith(

        f"user_{user.id}_"

    ):

        abort(

            403,

            description=
            "You cannot download another user's export"

        )

    return send_from_directory(

        "exports",

        filename,

        as_attachment=True

    )


# =============================================================================
# ERROR HANDLERS
# =============================================================================
#
# Automatically returns custom JSON
# whenever these errors occur.
#
# =============================================================================

# Forbidden.
@app.errorhandler(403)

def forbidden(e):

    return jsonify({

        "message":
        "Forbidden - You do not have permission to access this resource"

    }),403


# Page Not Found.
@app.errorhandler(404)

def not_found(e):

    return jsonify({

        "message":
        "Not Found"

    }),404


# Internal Server Error.
@app.errorhandler(500)

def internal_server_error(e):

    return jsonify({

        "message":
        "Internal Server Error"

    }),500