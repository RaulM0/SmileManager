#!/bin/sh
set -eu

case "${1:-}" in
    runserver)
        python manage.py migrate --noinput
        set -- python manage.py "$@"
        ;;
    gunicorn)
        python manage.py migrate --noinput
        python manage.py collectstatic --noinput
        ;;
esac

exec "$@"
