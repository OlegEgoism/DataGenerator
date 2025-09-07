FROM python:3.10-slim

WORKDIR /app

# Сначала скопируем только requirements.txt (это ускоряет пересборку образа)
COPY requirements.txt /app/

# Установим зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем весь проект
COPY . /app

# Сделаем entrypoint исполняемым
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
