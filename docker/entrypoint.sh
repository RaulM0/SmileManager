#!/bin/sh
set -eu

if [ "${1:-}" = "runserver" ]; then
    python manage.py migrate --noinput
    exec python manage.py "$@"
fi

exec "$@"
