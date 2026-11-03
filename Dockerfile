# ---------- Stage 1: build the React frontend ----------
FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
# ajv@8 is required to build CRA5 on newer Node images
RUN npm install ajv@8.17.1 --legacy-peer-deps

COPY frontend/ ./
ENV CI=false
ENV GENERATE_SOURCEMAP=false
RUN npm run build

# ---------- Stage 2: Django runtime ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# Install Python dependencies first (better layer caching)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend and the built SPA
COPY backend/ backend/
COPY --from=frontend-build /app/frontend/build frontend/build

WORKDIR /app/backend

# Collect static files (whitenoise serves them in production)
RUN python manage.py collectstatic --noinput

# Use a non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Migrate then serve with gunicorn
CMD sh -c "python manage.py migrate --noinput && python manage.py seed_default_admin && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"
