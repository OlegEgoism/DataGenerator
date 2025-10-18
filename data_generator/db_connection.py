from __future__ import annotations
import psycopg2
from psycopg2 import OperationalError

try:
    import clickhouse_connect
except Exception:
    clickhouse_connect = None

from data_generator.models import AppSettings


def get_engine(project) -> str:
    """'postgres' или 'clickhouse' по полю Подключение."""
    try:
        name = (project.data_base_name.name or "").strip().lower()
    except Exception:
        name = ""
    return "clickhouse" if name in {"clickhouse", "ch"} else "postgres"


def close_connection(conn):
    """Аккуратно закрыть соединение любого типа."""
    if conn is None:
        return
    try:
        if hasattr(conn, "closed") and hasattr(conn, "close"):
            if not conn.closed:
                conn.close()
        elif hasattr(conn, "close"):
            conn.close()
    except Exception:
        pass


def get_db_connection(project):
    """Возвращает (conn_or_client, error_message)."""
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    engine = get_engine(project)

    if engine == "clickhouse":
        if clickhouse_connect is None:
            return None, "Установи пакет: pip install clickhouse-connect"
        try:
            client = clickhouse_connect.get_client(
                host=project.db_host or "localhost",
                port=int(project.db_port or 8123),
                username=project.db_user or "default",
                password=project.db_password or "",
                database=project.db_name or "default",
                connect_timeout=connect_timeout,
            )
            client.command("SELECT 1")
            return client, None
        except Exception as e:
            return None, f"ClickHouse connection error: {e}"

    # PostgreSQL
    try:
        conn = psycopg2.connect(
            dbname=project.db_name,
            user=project.db_user,
            password=project.db_password,
            host=project.db_host,
            port=project.db_port,
            connect_timeout=connect_timeout,
        )
        with conn.cursor() as cur:
            cur.execute("SELECT 1;")
        return conn, None
    except OperationalError:
        return None, "Ошибка подключения! Проверь настройки."
    except Exception as e:
        return None, f"Ошибка подключения: {e}"
