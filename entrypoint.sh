#!/usr/bin/env bash
set -e

# Применяем миграции (если db.sqlite3 нет — он создастся)
python manage.py migrate --noinput

# Опционально: собрать статические файлы (если используете)
# python manage.py collectstatic --noinput || true

# Опционально: автосоздание суперпользователя
if [ "${DJANGO_CREATE_SUPERUSER:-0}" = "1" ]; then
python <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "project.settings"))
from django.contrib.auth import get_user_model
User = get_user_model()
u = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
e = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
p = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")
if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, e, p)
    print(f"Superuser created: {u}")
else:
    print(f"Superuser already exists: {u}")
PY
fi

# Запуск основного процесса
exec "$@"
