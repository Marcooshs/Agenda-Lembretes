#!/usr/bin/env bash
set -e

role="$1"

wait_for() {
  host="$1"; port="$2"; name="$3"
  echo "Aguardando ${name} em ${host}:${port}..."
  for i in {1..60}; do
    nc -z "$host" "$port" && echo "${name} disponível!" && return 0
    sleep 1
  done
  echo "Timeout ao aguardar ${name}."
  exit 1
}

if [ -f '.env' ]; then
  export $(grep -v '^#' .env | xargs)
fi

DB_HOST=$(python - <<'PY'
import os, re
url=os.environ.get('DATABASE_URL','')
m=re.match(r'.*?://.*?@([^:/]+)(?::(\d+))?/', url)
print((m.group(1) if m else 'db'))
PY
)
DB_PORT=$(python - <<'PY'
import os, re
url=os.environ.get('DATABASE_URL','')
m=re.match(r'.*?://.*?@[^:/]+:(\d+)/', url)
print((m.group(1) if m else '5432'))
PY
)

if [ "$role" != 'worker' ] && [ "$role" != 'beat' ]; then
  wait_for "$DB_HOST" "$DB_PORT" 'Postgres'
fi

if [ -n "$REDIS_URL" ]; then
  REDIS_HOST=$(python - <<'PY'
import os,urllib.parse as up
u=up.urlparse(os.environ.get('REDIS_URL','redis://redis:6379/0'))
print(u.hostname or 'redis')
PY
)
  REDIS_PORT=$(python - <<'PY'
import os,urllib.parse as up
u=up.urlparse(os.environ.get('REDIS_URL','redis://redis:6379/0'))
print(u.port or 6379)
PY
)
  wait_for "$REDIS_HOST" "$REDIS_PORT" 'Redis'
fi

python manage.py migrate --noinput

if [ "$role" = 'web' ]; then
  mkdir -p static
  python manage.py collectstatic --noinput || true
  python manage.py runserver 0.0.0.0:8000
elif [ "$role" = 'worker' ]; then
  celery -A app worker -l info
elif [ "$role" = 'beat' ]; then
  celery -A app beat -l info --schedule /tmp/celerybeat-schedule
else
  exec "$@"
fi
