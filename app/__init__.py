from flask import Flask, render_template
from app.config import Config


# These are initialized later using init_app() to avoid circular imports.



from app.extensions import db, jwt, cors, init_redis, init_celery



# APPLICATION FACTORY
# This function creates and returns a Flask application object.
# This is called the Application Factory Pattern.
# - Allows multiple application instances.
# - Makes testing easier.
# - Avoids circular imports.
# - Recommended structure for medium/large Flask projects.

def create_app(config_class=Config):

    # Creates the Flask application object.
    app = Flask(__name__)

    # Loads configuration values from Config class.
    # SECRET_KEY, SQLALCHEMY_DATABASE_URI ,# JWT settings ,# Redis URL
    app.config.from_object(config_class)

    # Initialize all Flask extensions

    # Connect SQLAlchemy with Flask application.
    # After this, all models can communicate with the database.
    db.init_app(app)

    # Enables JWT token creation and verification.
    jwt.init_app(app)

    # Enable Cross-Origin Resource Sharing (CORS).
    # Allows frontend (React/HTML/JS) running on another origin
    # to access backend APIs.
    cors.init_app(app)

    # Initialize Redis connection.
    # Redis is mainly used for caching, session storage,
    # OTP storage, temporary data etc.
    init_redis(app)

    # Initialize Celery.
    # Celery is used for background tasks such as:
    # Sending emails
    # Notifications
    # Report generation
    #need to do the webhook 
    init_celery(app)

    # AUTHENTICATION BLUEPRINT
    # Blueprint is Flask's way of organizing routes.
    #
    # Instead of writing every API in one file,
    # authentication APIs are kept inside auth.py.
    #
    # Viva:
    # Q: What is a Blueprint?
    # A:
    # Blueprint is a modular component that groups related routes together.
    #
    from app.auth import auth_bp

    # Registers all authentication routes.
    app.register_blueprint(auth_bp)

    # =========================================================================
    # IMPORT OTHER ROUTES
    # =========================================================================
    #
    # routes.py registers APIs directly using current_app.
    #
    # Therefore it must be imported inside an application context.
    #
    # Viva:
    # Q: Why use app.app_context()?
    # Flask extensions like current_app, database, etc.
    # need an active application context.
    #
    with app.app_context():
        from app import routes      # noqa: F401

  
    # APIs are written separately.
  

    # LOGIN PAGE 
 
 
    @app.route("/")
    @app.route("/login")
    def page_login():
        # Shows login page.
        return render_template("login.html")

    # REGISTER PAGE 
    @app.route("/register")
    def page_register():
        # Shows registration page.
        return render_template("register.html")

    # ADMIN MODULE


    @app.route("/admin/dashboard")
    def page_admin_dashboard():
        # Admin dashboard.
        # active variable highlights current sidebar option.
        return render_template("admin_dashboard.html", active="dashboard")

    @app.route("/admin/treks")
    def page_admin_treks():
        # Page for managing treks.
        return render_template("admin_treks.html", active="treks")

    @app.route("/admin/staff")
    def page_admin_staff():
        # View all staff.
        return render_template("admin_staff.html", active="staff")

    @app.route("/admin/staff/new")
    def page_admin_staff_new():
        # Add new staff member.
        return render_template("admin_staff_new.html", active="staff")

    @app.route("/admin/users")
    def page_admin_users():
        # View all registered users.
        return render_template("admin_users.html", active="users")

    @app.route("/admin/bookings")
    def page_admin_bookings():
        # Manage all bookings.
        return render_template("admin_bookings.html", active="bookings")

    @app.route("/admin/search")
    def page_admin_search():
        # Search users/bookings/treks.
        return render_template("admin_search.html", active="search")

    @app.route("/admin/reports")
    def page_admin_reports():
        # Reports and analytics page.
        return render_template("admin_reports.html", active="reports")

    # STAFF MODULE
    
    @app.route("/staff/dashboard")
    def page_staff_dashboard():
        # Staff dashboard.
        return render_template("staff_dashboard.html", active="dashboard")

    @app.route("/staff/treks")
    def page_staff_treks():
        # Shows treks assigned to staff.
        return render_template("staff_dashboard.html", active="mytreks")

    @app.route("/staff/profile")
    def page_staff_profile():
        # Staff profile page.
        return render_template("staff_profile.html", active="profile")

    @app.route("/staff/treks/<int:trek_id>/participants")
    def page_staff_participants(trek_id):

        # Dynamic route.
        #
        # <int:trek_id> captures trek ID from URL.
        #
        # Example:
        # /staff/treks/5/participants
        #
        # trek_id = 5
        #
        return render_template(
            "staff_participants.html",
            active="participants",
            trek_id=trek_id
        )

    @app.route("/staff/treks/<int:trek_id>")
    def page_staff_manage_trek(trek_id):

        # Dynamic page for managing a particular trek.
        return render_template(
            "staff_manage_trek.html",
            active="mytreks",
            trek_id=trek_id
        )

    # USER MODULE
    
    @app.route("/user/dashboard")
    def page_user_dashboard():
        # User dashboard.
        return render_template("user_dashboard.html", active="dashboard")

    @app.route("/user/bookings")
    def page_user_bookings():
        # User's current bookings.
        return render_template("user_bookings.html", active="bookings")

    @app.route("/user/browse")
    def page_user_browse():
        # Browse available treks.
        return render_template("user_browse.html", active="browse")

    @app.route("/user/history")
    def page_user_history():
        # Shows completed bookings.
        return render_template("user_history.html", active="history")

    @app.route("/user/profile")
    def page_user_profile():
        # User profile page.
        return render_template("user_profile.html", active="profile")

    # Return the fully configured Flask application.
    # Flask will use this object to start the server.
    return app