#!/bin/sh
set -e

# --skip-checks: system checks import every URL module; code that queries the DB at import time
# (choices=Model.objects...) would crash migrate on the first deploy, before the tables exist.
python manage.py migrate --noinput --skip-checks

# 1 worker × 4 threads (gthread): threads share the worker's RAM; change with env GUNICORN_WORKERS/THREADS.
# GUNICORN_TIMEOUT: keep the old server's --timeout (VPS 2 apps ran 300) for slow views.
exec gunicorn Project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-1}" \
    --threads "${GUNICORN_THREADS:-4}" \
    --timeout "${GUNICORN_TIMEOUT:-300}" \
    --access-logfile -
