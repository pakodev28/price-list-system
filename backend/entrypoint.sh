#!/usr/bin/env sh
set -e

# Apply committed migrations before starting the server.
# Only the backend service runs this entrypoint; the worker skips it.
python manage.py migrate --noinput

exec "$@"
