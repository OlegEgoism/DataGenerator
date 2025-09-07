FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Сначала зависимости (ускоряет пересборку)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Затем весь проект
COPY . /app

# Создаём entrypoint исполняемым
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Значения по умолчанию — включаем авто-создание superuser
ENV DJANGO_CREATE_SUPERUSER=1 \
    DJANGO_SUPERUSER_USERNAME=admin \
    DJANGO_SUPERUSER_EMAIL=admin@example.com \
    DJANGO_SUPERUSER_PASSWORD=admin

# Если модуль настроек отличается от conf.settings — переопределите переменной окружения
ENV DJANGO_SETTINGS_MODULE=conf.settings

ENTRYPOINT ["/entrypoint.sh"]

# dev-сервер по умолчанию; для prod используйте gunicorn/uvicorn
CMD ["python", "manage.py", "runserver", "127.0.0.1:8000"]
