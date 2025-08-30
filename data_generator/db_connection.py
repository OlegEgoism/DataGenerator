import psycopg2

from data_generator.models import AppSettings


def get_db_connection(project):
    """Соединение с базой данных"""
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    try:
        connection = psycopg2.connect(
            dbname=project.db_name,
            user=project.db_user,
            password=project.db_password,
            host=project.db_host,
            port=project.db_port,
            connect_timeout=connect_timeout
        )
        return connection, None
    except Exception as e:
        return None, f"Ошибка подключения: {str(e)}"

