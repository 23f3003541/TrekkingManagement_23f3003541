"""
Programmatic DB bootstrap: creates all tables (no manual DB Browser edits allowed
per your brief) and seeds the single Admin account.

The table creation call itself works as soon as your models exist. The
`create_admin(...)` call depends on app/auth.py, which is a stub — implement
that first, then run:

    python seed.py
"""
from app import create_app
from app.extensions import db
from app.auth import create_admin

app = create_app()

with app.app_context():
    db.create_all()
    print("Tables created.")

    # TODO: pick real admin credentials (ideally from env vars, not hardcoded)
    create_admin(email="a@tm", password="123", full_name="System Admin")
    print("Admin account ensured.")
