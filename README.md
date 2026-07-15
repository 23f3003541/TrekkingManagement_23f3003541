# Trekking Management Application (TMA) — V2

Stack: **Flask** (API) + **Jinja2 entry point + VueJS via CDN** (UI, no build step) +
**Bootstrap** (styling) + **SQLite** (DB) + **Redis** (cache) + **Redis/Celery** (batch jobs).

## Status: fully implemented, working end-to-end

Every layer — models, auth, routes, Celery jobs, caching, and the Bootstrap/Vue
frontend — is implemented and wired together. Before you submit this, **read
through every file and be ready to explain and modify each one at the viva** —
the brief explicitly requires the schema/business logic to be your own
understanding, not something you can only recite.

### What's implemented
- Flask app factory, config, folder structure (`app/__init__.py`, `app/config.py`)
- `app/models.py` — `User` (unified role field: admin/staff/user), `StaffProfile`,
  `Trek`, `Booking`, with the FK relationships and constraints (unique
  user+trek booking, cascades) needed to satisfy the brief's business rules
- `app/auth.py` — registration, JWT login, `role_required()` RBAC decorator,
  programmatic single-admin bootstrap, and staff-account creation (admin-only,
  no staff self-registration) — passwords hashed with `bcrypt`
- `app/routes.py` — all Admin / Staff / User API endpoints (single file, not
  split into a `routes/` package)
- `app/cache.py` — Redis caching layer with expiry, wired into the trek
  listing endpoint, invalidated on every trek write. Every Redis call is
  wrapped so a connection failure (e.g. `redis-server` not started yet)
  logs a warning and falls through to an uncached response instead of
  500ing the request — verified by testing `/api/treks` with Redis down
  and back up
- `app/tasks.py` — all three required Celery jobs:
  - Daily trek reminders sent via Google Chat webhook (`GCHAT_WEBHOOK_URL`),
    falls back to console output if not configured, for local demo
  - Monthly HTML activity report emailed to Admin via SMTP (`MAIL_*` config),
    same local-demo fallback
  - User-triggered async CSV export, polled via `/api/user/export-history/status/<task_id>`
    and downloaded via `/api/user/export-history/download/<filename>`
  - Both scheduled jobs are registered on **Celery Beat** (`app/extensions.py`)
- Full Bootstrap + Vue (CDN) frontend for every screen in the wireframe,
  including trek search/filter, staff assignment, blacklist toggles, profile
  editing, and the CSV export flow with real completion polling

## Important IDs to know when reading the code
`Trek.assigned_staff_id` is a foreign key to **`StaffProfile.id`**, not
`User.id`. `GET /api/admin/staff` returns both `id` (User.id, used for
blacklist/whitelist) and `staff_profile_id` (used to assign a trek) — the
admin treks UI dropdown uses `staff_profile_id`.

## Folder structure
```
tma/
├── run.py
├── seed.py                  # creates tables + the single admin
├── requirements.txt
├── app/
│   ├── __init__.py           # app factory
│   ├── config.py
│   ├── extensions.py         # db, redis, celery (+ beat schedule), jwt
│   ├── models.py
│   ├── auth.py
│   ├── routes.py             # all API routes (admin/staff/user/shared)
│   ├── tasks.py               # the three Celery jobs
│   ├── cache.py               # Redis caching helpers
│   ├── templates/             # Jinja2 + Vue CDN pages
│   └── static/
│       ├── css/style.css      # green/mountain theme
│       └── js/                # one Vue "app" per page
```

## Running locally
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

redis-server &                                   # terminal 1
python seed.py                                   # creates tables + admin (a@tm / 123 by default — change before demo)
celery -A app.extensions.celery worker --beat -l info &   # terminal 2
python run.py                                    # terminal 3
```

Default admin credentials are set in `seed.py` (`email="a@tm"`, `password="123"`)
— change these to something real before recording your demo video.

## Notes on the two "optional but real-world" jobs
- If you don't have a Google Chat webhook or SMTP credentials handy for the
  demo, leave `GCHAT_WEBHOOK_URL` / `MAIL_USERNAME` / `MAIL_PASSWORD` unset in
  your environment — both jobs will print the message/report to the console
  instead of failing, so you can still demo them live.
