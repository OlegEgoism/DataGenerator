#!/usr/bin/env bash
set -e

# 1) Сгенерировать миграции для всех приложений (если их ещё нет)
python manage.py makemigrations --noinput || true

# 2) Применить миграции
python manage.py migrate --noinput

# (опционально) собрать статику
# python manage.py collectstatic --noinput || true

# === 1) Автосоздание суперпользователя ======================================
if [ "${DJANGO_CREATE_SUPERUSER:-0}" = "1" ]; then
python <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "project.settings"))
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()
u = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin")
e = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com")
p = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin")

if not User.objects.filter(username=u).exists():
    User.objects.create_superuser(u, e, p)
    print(f"[init] Superuser created: {u}")
else:
    print(f"[init] Superuser already exists: {u}")
PY
fi

# === 2) Инициализация записей DataBaseName ===================================
# Найдём модель DataBaseName динамически (без жёсткой привязки к имени приложения)
python <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.getenv("DJANGO_SETTINGS_MODULE", "project.settings"))
django.setup()

from django.apps import apps

Model = None
for m in apps.get_models():
    if m.__name__ == "DataBaseName":
        Model = m
        break

if not Model:
    print("[init] Model DataBaseName not found — пропускаю инициализацию.")
else:
    names = ["Hive", "Greenplum", "MySql", "Oracle", "PostgreSQL", "ClickHouse"]
    for nm in names:
        obj, created = Model.objects.get_or_create(name=nm)
        if created:
            # Ваша переопределённая .save() сама подставит images_db из маппинга
            print(f"[init] DataBaseName created: {nm}")
        else:
            # При желании можно форс-обновить images_db по вашему маппингу:
            # obj.save()
            print(f"[init] DataBaseName exists: {nm}")
PY

# Запуск основного процесса
exec "$@"
