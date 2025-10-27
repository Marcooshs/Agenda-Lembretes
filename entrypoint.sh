#!/usr/bin/env bash
set -euo pipefail

role="${1:-web}"

wait_for() {
  local host="$1" port="$2"
  echo "Aguardando ${host}:${port}..."
  until nc -z -w 1 "$host" "$port"; do
    sleep 1
  done
  echo "${host}:${port} disponivel."
}

# Sempre espere o Postgres
wait_for db 5432

# Para worker/beat, tambem espere o Redis
if [[ "$role" != "web" ]]; then
  wait_for redis 6379
fi

python manage.py migrate --noinput

case "$role" in
  web)
    # Se voce usa STATIC_ROOT, o collectstatic funciona.
    # Caso nao use, pode comentar a linha abaixo.
    python manage.py collectstatic --noinput
    exec python manage.py runserver 0.0.0.0:8000
    ;;
  worker)
    exec celery -A app.celery worker -l info
    ;;
  beat)
    exec celery -A app.celery beat -l info
    ;;
  *)
    exec "$@"
    ;;
esac
