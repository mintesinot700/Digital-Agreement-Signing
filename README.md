# Digital Agreement Signing

A robust, cloud-based platform for secure, legally compliant, and instantaneous
electronic signing of documents and contracts. Built with **Django 5 + Django
REST Framework** (backend) and **React (Create React App)** (frontend).

## Features

- **User registration & JWT authentication** — access tokens in memory,
  refresh token in an HttpOnly cookie, silent refresh on expiry, logout with
  refresh-token blacklisting.
- **Agreement templates** — admins upload agreement PDFs; users browse and
  read them in an embedded viewer before signing.
- **Agreement submission** — users fill personal details, upload a profile
  photo and ID photo, and **draw their signature** on a signature pad
  (works with mouse and touch).
- **Admin dashboard** — review agreements, approve/reject with a click,
  manage users, upload/edit/delete PDF templates.
- **Summary PDF generation** — one-click download of a printable agreement
  summary document including the captured signature.
- **Email notifications** — submission confirmations and status-change
  notifications (approve/reject) sent to the signer's email.
- **Audit trail** — every create/update/status-change/delete/PDF-download is
  recorded with actor, timestamp and details, visible in the dashboard and
  the Django admin.
- **Production-ready** — environment-driven settings, WhiteNoise static
  serving, Gunicorn, Docker & docker-compose deployment, plus a one-click
  Render Blueprint (`render.yaml`).
- **Test suite** — 45 API tests covering auth, submission, review, PDF
  generation, audit trail and email notifications.
- **Signer visibility** — users see every agreement they submitted with its
  live status and can download the summary PDF from the "My Submissions"
  panel.

## Project structure

```
├── backend/                  # Django project
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/               # Django settings/urls (project package)
│   ├── accounts/             # Custom user model, auth API (JWT login/refresh/logout)
│   └── agreement/            # Agreements, PDF templates, audit log, PDF service
│       ├── models.py         # Agreement, Pdf_agreement, AuditLog
│       ├── serializers.py    # DRF serializers (validation)
│       ├── pdf_service.py    # ReportLab summary-PDF generator
│       ├── signals.py        # Audit logging + email notifications
│       └── files/            # Bundled sample PDFs (seeded as templates on boot)
├── frontend/                 # React app (CRA)
├── Dockerfile                # Multi-stage: React build + Django runtime
├── docker-compose.yml        # web + PostgreSQL
├── render.yaml               # One-click Render Blueprint (web + Postgres)
└── .env.example              # Environment variable template
```

Uploaded media lives in `backend/media/` (gitignored).

## API overview

| Endpoint | Method | Auth | Description |
|---|---|---|---|
| `/api/token/` | POST | public | Login (returns access + user info, sets refresh cookie) |
| `/api/token/refresh/` | POST | cookie | Rotate refresh token, issue new access token |
| `/api/user/logout/` | POST | JWT | Blacklist refresh token, clear cookie |
| `/api/user/register/` | POST | public | Create an account |
| `/api/verify-admin/` | GET | JWT | Check admin status |
| `/api/agreement/` | POST | JWT | Submit an agreement (multipart) |
| `/api/my-agreements/` | GET | JWT | List the current user's agreements |
| `/api/agreement_list/` | GET | admin | List all agreements (`?status=`, `?search=`) |
| `/api/agreement/<id>/` | GET/PATCH/DELETE | admin | Retrieve / approve / reject / delete |
| `/api/agreement/<id>/pdf/` | GET | owner/admin | Download generated summary PDF |
| `/api/pdf_agreement/` | GET | public | List agreement templates |
| `/api/pdf_agreement/create/` | POST | admin | Upload a template PDF |
| `/api/pdf_agreement/<id>/` | PATCH/DELETE | admin | Edit / delete a template |
| `/api/pdf/<id>/` | GET | public | Serve a template PDF (iframe-friendly) |
| `/api/audit-log/` | GET | admin | Audit trail entries |
| `/django-admin/` | — | staff | Django admin |

## Local development (without Docker)

**Backend**

```bash
cd backend
python -m venv ../.venv && source ../.venv/bin/activate   # Windows: ..\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser      # or: python manage.py seed_default_admin
python manage.py runserver        # http://127.0.0.1:8000
```

By default the project uses **SQLite** — no database setup needed. Emails are
printed to the console in development.

**Frontend**

```bash
cd frontend
npm install --legacy-peer-deps
npm start                         # http://localhost:3000 (CORS is pre-configured)
```

Set `REACT_APP_API_URL=http://127.0.0.1:8000/` in the React app's environment
if the API runs somewhere else.

## Running the tests

```bash
cd backend
python manage.py test
```

60 tests, no external services required (SQLite + in-memory email backend):

- **accounts** — registration (incl. duplicate-username rejection),
  case-insensitive login, refresh-cookie rotation, logout blacklisting,
  admin verification, user management permissions, password-hash exposure.
- **agreement** — submission with image validation, ownership-scoped
  "my agreements", admin review with status filter/search, audit-trail
  entries for every action, email notifications, summary-PDF download
  permissions.

## Production deployment

### Option A — Render (one click)

The repo ships a Render Blueprint (`render.yaml`) that provisions the web
service (built from the Dockerfile) and a PostgreSQL database:

1. Push this repository to GitHub.
2. In [Render](https://dashboard.render.com): **New → Blueprint** and select
   the repository (or run `render blueprint launch` from a clone).
3. Render builds the image, runs migrations and serves the app on HTTPS.
4. Create the first admin: open the Render **Shell** tab and run
   `python manage.py createsuperuser`.

Free-plan notes: uploaded media is ephemeral (see the disk comment in
`render.yaml`), and the free database expires after 30 days — upgrade to a
paid plan (or attach a disk + use SQLite) for durable data.

### Option B — Docker Compose (recommended for your own server)

```bash
cp .env.example .env
# edit .env: set SECRET_KEY, POSTGRES_PASSWORD, ALLOWED_HOSTS,
#            CORS_ALLOWED_ORIGINS, email credentials
docker compose up -d --build
docker compose exec web python manage.py createsuperuser
```

The app is served at `http://<host>:8000` — Django serves both the REST API
and the built React app, behind Gunicorn + WhiteNoise.

### Option C — any VPS / PaaS (Railway, Fly.io, …)

1. Provision PostgreSQL and set `DATABASE_URL=postgres://...`
2. Set the environment variables from `.env.example`
3. Build command: `pip install -r backend/requirements.txt && cd frontend && npm install --legacy-peer-deps && npm install ajv@8.17.1 --legacy-peer-deps && npm run build && cd ../backend && python manage.py collectstatic --noinput`
4. Start command: `cd backend && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
5. Migrate once: `cd backend && python manage.py migrate`

### Environment variables (all optional except in production)

| Variable | Default | Purpose |
|---|---|---|
| `SECRET_KEY` | insecure dev key | Django secret — **must** be set in production |
| `DEBUG` | `False` | Debug mode |
| `ALLOWED_HOSTS` | localhost | Comma-separated hosts |
| `DATABASE_URL` / `POSTGRES_*` | SQLite | Database configuration |
| `CORS_ALLOWED_ORIGINS` | localhost:3000 | Frontend origins |
| `COOKIE_SECURE` | `not DEBUG` | Secure refresh cookie (set `True` behind HTTPS) |
| `COOKIE_SAMESITE` | `Lax` | `Lax` or `None` (cross-site deployments) |
| `EMAIL_BACKEND` | console | Set to `django.core.mail.backends.smtp.EmailBackend` in production |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_USE_TLS` | — | SMTP settings |
| `DEFAULT_FROM_EMAIL` | no-reply@example.com | Sender for notifications |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` / `ADMIN_EMAIL` | `admin` / `Admin@12345` / admin@example.com | Bootstrap superuser created on boot **only when the database has no superuser** — change the password in production. Setting `ADMIN_PASSWORD` also **rotates** the bootstrap admin's password on the next boot |
| `SEED_SAMPLE_TEMPLATES` | `1` | Set to `0` to stop the boot command from creating `Pdf_agreement` rows for the PDFs bundled in `agreement/files/` (fresh installs otherwise have no template to submit against) |

## Notes

- The database (`db.sqlite3`), uploaded media and the React build are
  **not tracked in git** — see `.gitignore`.
- If your deployment is cross-site (frontend and API on different domains),
  set `COOKIE_SAMESITE=None`, `COOKIE_SECURE=True` and both `CORS_ALLOWED_ORIGINS`
  and `CSRF_TRUSTED_ORIGINS` to your frontend origin.
- Historical git commits may still contain previously committed secrets —
  rotate any credentials that were committed before this hardening pass.
