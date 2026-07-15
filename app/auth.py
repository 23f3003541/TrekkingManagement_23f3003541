from functools import wraps

# bcrypt is used for secure password hashing.
import bcrypt

from flask import Blueprint, jsonify, request

# JWT library functions
from flask_jwt_extended import (
    create_access_token,
    get_jwt_identity,
    jwt_required,
)

# Database models
from app.models import StaffProfile, User

# SQLAlchemy database object
from app.extensions import db


# AUTHENTICATION BLUEPRINT

# Blueprint is used to organize authentication-related APIs separately.
#
# url_prefix="/api/auth"
#
# Therefore:
# /login  -> /api/auth/login
# /register -> /api/auth/register
#
auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


# PASSWORD HASHING
#what technique we used solve the password
# Converts a plain password into a secure hashed password.
#

#
# Viva:
# Q: Why hash passwords?
#
# A:
# Passwords should never be stored in plain text because if the
# database is compromised, attackers cannot immediately know users'
# passwords.
#
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


# PASSWORD VERIFICATION

# Compares entered password with stored hashed password.
#
# Returns:
# True  -> Password matches
# False -> Incorrect password
#
def _check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


# REGISTER USER

# POST /api/auth/register

@auth_bp.route("/register", methods=["POST"])
def register():

    # Reads JSON data from request body.
    data = request.get_json()

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    contact_number = data.get("contact_number")


    # Checks required fields.

    #compulsory fields can change settings from here 


    if not all([full_name, email, password]):
        return jsonify({"message": "Missing required fields"}), 400

    # Checks if email already exists.
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email already exists"}), 409

    # Hash password before saving.
    password_hash = _hash_password(password)

    # Create new User object.
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        contact_number=contact_number,
        role="user",
        status="Active",
    )

    # Save user into database.
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Registration successful"}), 201


# LOGIN
#  POST /api/auth/login
#
# Steps:
# 1. Read email/password
# 2. Find user
# 3. Check account status
# 4. Verify password
# 5. Generate JWT Token
# 6. Send dashboard URL


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    # Search user by email.
    user = User.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"message": "User Not found "}), 401

    # Prevent blocked users from logging in.
    if user.status == "Blacklisted":
        return jsonify({"message": "Account has been blocked"}), 403

    # Verify password.
    if not _check_password(password, user.password_hash):
        return jsonify({"message": "Password incorrect"}), 401

    # Generate JWT token.
    #
    # Identity stores user ID.
    # Additional claims store user role.

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={
            "role": user.role
        }
    )

    # Redirect based on role.
    if user.role == "admin":
        redirect_to = "/admin/dashboard"

    elif user.role == "staff":
        redirect_to = "/staff/dashboard"

    else:
        redirect_to = "/user/dashboard"

    # Return login response.
    return jsonify(
        {
            "access_token": access_token,
            "role": user.role,
            "user_id": user.id,
            "name": user.full_name,
            "redirect": redirect_to,
        }
    )


# ROLE-BASED AUTHORIZATION DECORATOR

# Used to restrict APIs based on user roles.
#
# Example:
#
# @role_required("admin")
#
# Only admins can access.
#
# @role_required("admin","staff")
#
# Both admin and staff can access.
#
# What is a decorator?
# A decorator modifies the behavior of another function without changing
# its original code.
#
def role_required(*roles):

    def decorator(fn):

        @wraps(fn)

        # JWT token is mandatory.
        @jwt_required()
        def wrapper(*args, **kwargs):

            # Get logged-in user.
            user = get_current_user()

            if user is None:
                return jsonify({"message": "Unauthorized"}), 401

            # Check account status.
            if user.status == "Blacklisted":
                return jsonify({"message": "Account blocked"}), 403

            # Check allowed roles.
            if user.role not in roles:
                return jsonify({"message": "Forbidden"}), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator


# GET CURRENT LOGGED-IN USER

# Reads user ID stored inside JWT token.
#
# Returns User object.
#
def get_current_user():

    user_id = get_jwt_identity()

    if user_id is None:
        return None

    return User.query.get(int(user_id))


# CREATE DEFAULT ADMIN
def create_admin(email, password, full_name="Admin"):

    # Check existing admin.
    admin = User.query.filter_by(role="admin").first()

    if admin:
        return admin

    password_hash = _hash_password(password)

    admin = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        role="admin",
        status="Active",
    )

    db.session.add(admin)
    db.session.commit()

    return admin


# CREATE STAFF ACCOUNT
# Admin creates staff accounts.

# Creates:
# 1. User table entry
# 2. StaffProfile table entry
#
# Both are created in one transaction.
#


# why here not in admin.py because
# admin.py is for routes and this is a function that can be used in multiple places, not just in the admin routes. It is better to keep it in auth.py where authentication and user management functions are defined.
def create_staff_account(
        full_name,
        email,
        password,
        contact_number=None,
        experience=None,
        specialization=None):

    # Check duplicate email.
    if User.query.filter_by(email=email).first():
        raise ValueError("Email already exists")

    password_hash = _hash_password(password)

    # Create User table entry.
    user = User(
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        contact_number=contact_number,
        role="staff",
        status="Active",
    )

    db.session.add(user)

    # flush() writes pending changes to database
    # without committing.
    # It generates user.id immediately.
    db.session.flush()

    # Create StaffProfile linked with user.id.
    profile = StaffProfile(
        user_id=user.id,
        experience=experience,
        specialization=specialization,
        status="Active",
    )

    db.session.add(profile)

    # Save both records permanently.
    db.session.commit()

    return user