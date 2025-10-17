#!/usr/bin/env bash
set -e

role="$1"

echo 'Aguardando Postgres em db:5432...'
until nc -z db 5432; do
  sleep 1
done
echo 'Postgres disponível.'

python manage.py migrate --noinput

if [ "$role" = 'web' ]; then
  python manage.py collectstatic --noinput
  python manage.py runserver 0.0.0.0:8000
elif [ "$role" = 'worker' ]; then
  celery -A app.celery worker -l info
elif [ "$role" = 'beat' ]; then
  celery -A app.celery beat -l info
else
  exec "$@"
fi
