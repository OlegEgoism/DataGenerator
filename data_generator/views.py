import re

import clickhouse_connect
import psycopg2
import csv, io
from django.contrib.auth import logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.urls import reverse
from psycopg2 import sql
from django.http import StreamingHttpResponse, HttpResponseBadRequest
from django.utils import timezone
from faker import Faker
from data_generator.data_choices_list import choices_list, generate_fake_value, ALLOWED_TYPES, ALL_CHOICES, IDENT_RE
from data_generator.forms import CustomUserCreationForm, CustomUserForm, DataBaseUserForm
from data_generator.models import DataBaseUser, AppSettings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from data_generator.db_connection import get_db_connection, get_engine, close_connection


def home(request):
    """Главная"""
    return render(request,
                  template_name='home.html'
                  )


# TODO АВТОРИЗАЦИЯ/РЕГИСТРАЦИЯ
def register(request):
    """Регистрация"""
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request, "Регистрация прошла успешно!")
            return redirect("home")
        else:
            pass
    else:
        form = CustomUserCreationForm()
    return render(request,
                  template_name="registration/register.html",
                  context={"form": form}
                  )


def logout_view(request):
    """Выход"""
    logout(request)
    return redirect('home')


# TODO ПРОФИЛЬ
@login_required
def profile(request):
    """Профиль"""
    search_query = request.GET.get("search", "").strip()
    user_databases = DataBaseUser.objects.filter(user=request.user)
    uc = user_databases.count()
    if search_query:
        user_databases = user_databases.filter(db_project__icontains=search_query)
    return render(request,
                  template_name='profile.html',
                  context={
                      'user': request.user,
                      'user_databases': user_databases,
                      'search_query': search_query}
                  )


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    user = request.user
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно отредактирован.")
            return redirect('profile_edit')
        else:
            messages.warning(request, "Ошибка при редактировании профиля. Проверьте введенные данные.")
    else:
        form = CustomUserForm(instance=user)
    return render(request,
                  template_name='profile_edit.html',
                  context={'user': user,
                           'form': form}
                  )


# TODO ПРОЕКТЫ
@login_required
def projects(request):
    """Проекты"""
    search_query = request.GET.get("search", "").strip()
    paginator_projects = AppSettings.objects.first()
    projects = DataBaseUser.objects.filter(user=request.user)
    if search_query:
        projects = projects.filter(Q(db_project__icontains=search_query) | Q(db_name__icontains=search_query))
    projects = projects.order_by("-updated")
    page_size = paginator_projects.paginator_projects if paginator_projects else 4
    paginator = Paginator(projects, page_size)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request,
                  template_name="projects.html",
                  context={
                      "projects": page_obj,
                      "search_query": search_query}
                  )


@login_required
def project_create(request):
    """Создание проекта"""
    user = request.user
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = user
            project.save()
            messages.success(request, "Проект успешно создан!", extra_tags="alert alert-success")
            return redirect('projects')
    else:
        form = DataBaseUserForm()
    return render(request,
                  template_name='project_create.html',
                  context={
                      'form': form}
                  )


@login_required
def project_delete(request, pk: int):
    """Удаление проекта"""
    project = get_object_or_404(DataBaseUser, pk=pk, user=request.user)
    if request.method == "POST":
        next_url = request.POST.get("next") or reverse("projects")
        project_name = project.db_project
        project.delete()
        messages.success(request, f'Проект «{project_name}» удалён.')
        return redirect(next_url)
    return redirect("projects")


@login_required
def project_edit(request, pk):
    """Редактирование проекта"""
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    database = get_object_or_404(DataBaseUser, pk=pk, user=request.user)
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST, instance=database)
        if form.is_valid():
            old_password = DataBaseUser.objects.get(pk=pk).db_password
            db_obj = form.save(commit=False)
            if not form.cleaned_data.get('db_password'):
                db_obj.db_password = old_password
            db_obj.save()
            if 'check_connection' in request.POST:
                conn, error = get_db_connection(db_obj)
                if conn is not None:
                    close_connection(conn)
                    messages.success(request, f"Успешное подключение к базе данных «{db_obj.db_name}».")
                else:
                    messages.warning(request, f"Ошибка подключения: {error}")
                form = DataBaseUserForm(instance=db_obj)
                form.fields['db_password'].initial = db_obj.db_password
                form.fields['db_password'].widget.attrs['value'] = db_obj.db_password
                return render(request, 'projects_edit.html', {'form': form, 'database': db_obj})
            messages.success(request, "Данные успешно сохранены.")
            return redirect(reverse('projects_edit', args=[db_obj.pk]))
        else:
            messages.warning(request, "Исправьте ошибки в форме.")
    else:
        form = DataBaseUserForm(instance=database)
        form.fields['db_password'].initial = database.db_password
        form.fields['db_password'].widget.attrs['value'] = database.db_password
    return render(request,
                  template_name='projects_edit.html',
                  context={
                      'form': form,
                      'database': database}
                  )


@login_required
def project_connection(request, pk: int):
    """Синхронизация проекта (проверка подключения к БД)"""
    project = get_object_or_404(DataBaseUser, pk=pk, user=request.user)
    next_url = request.POST.get("next") or reverse("projects")
    if request.method != "POST":
        return redirect(next_url)
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    engine = get_engine(project)
    try:
        if engine == "clickhouse":
            if clickhouse_connect is None:
                messages.warning(request, "Пакет clickhouse-connect не установлен.")
                return redirect(next_url)
            client = clickhouse_connect.get_client(
                host=project.db_host or "localhost",
                port=int(project.db_port or 8123),
                username=project.db_user or "default",
                password=project.db_password or "",
                database=project.db_name or "default",
                connect_timeout=connect_timeout,
            )
            client.command("SELECT 1")
            client.close()
            messages.success(request, f"Успешное подключение к ClickHouse базе «{project.db_name}».")
        else:
            conn = psycopg2.connect(
                dbname=project.db_name,
                user=project.db_user,
                password=project.db_password,
                host=project.db_host,
                port=project.db_port,
                connect_timeout=connect_timeout,
            )
            conn.close()
            messages.success(request, f"Успешное подключение к базе данных «{project.db_name}».")
    except Exception as e:
        messages.warning(request, f"Ошибка подключения: {str(e)}")

    return redirect(next_url)


# TODO СХЕМЫ
@login_required
def database_schemas(request, pk):
    """Схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    search_query = (request.GET.get("search") or "").strip()
    schemas, error_message = [], None
    conn, error_message = get_db_connection(project)
    engine = get_engine(project)
    if conn:
        try:
            if get_engine(project) == "clickhouse":
                rows = conn.query("""
                    SELECT name
                    FROM system.databases
                    WHERE name NOT IN ('system', 'INFORMATION_SCHEMA', 'information_schema')
                    ORDER BY name
                """).result_rows
                schemas = [r[0] for r in rows]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT schema_name
                        FROM information_schema.schemata
                        WHERE schema_name NOT IN ('pg_toast','pg_catalog','information_schema')
                        ORDER BY schema_name
                    """)
                    schemas = [r[0] for r in cursor.fetchall()]
        except Exception as e:
            error_message = f"Ошибка получения списка схем: {e}"
        finally:
            close_connection(conn)
    if search_query:
        q = search_query.lower()
        schemas = [s for s in schemas if q in s.lower()]
    return render(request,
                  template_name="database_schemas.html",
                  context={
                      "project": project,
                      "schemas": schemas,
                      "error_message": error_message,
                      "search_query": search_query,
                      "engine": engine
                  })


@login_required
def database_schemas_create(request, pk):
    """Создание схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    if request.method == "POST":
        schema_name = (request.POST.get("schema_name") or "").strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            messages.warning(
                request,
                "Название может содержать только латинские буквы, цифры и «_», и не может начинаться с цифры."
            )
            return redirect("database_schemas_create", pk=pk)
        conn, error_message = get_db_connection(project)
        if not conn:
            messages.warning(request, error_message or "Ошибка подключения к БД.")
            return redirect("database_schemas_create", pk=pk)
        engine = get_engine(project)

        try:
            if engine == "clickhouse":
                try:
                    result = conn.query("SELECT value FROM system.settings WHERE name = 'readonly'")
                    ro_value = result.result_rows[0][0] if result.result_rows else '0'
                    if int(ro_value) != 0:
                        messages.warning(request, "ClickHouse в режиме readonly — создание баз данных запрещено.")
                        return redirect("database_schemas_create", pk=pk)
                except Exception:
                    pass
                result = conn.query(
                    "SELECT count() FROM system.databases WHERE name = %(n)s",
                    parameters={"n": schema_name},
                )
                exists = result.result_rows[0][0] if result.result_rows else 0
                if int(exists) > 0:
                    messages.warning(request, f"База данных (схема) «{schema_name}» уже существует!")
                    return redirect("database_schemas_create", pk=pk)
                try:
                    conn.command(f"CREATE DATABASE `{schema_name}` ENGINE = Atomic")
                except Exception as e:
                    msg = str(e).lower()
                    if "unknown" in msg or "engine" in msg:
                        conn.command(f"CREATE DATABASE `{schema_name}`")
                    else:
                        raise
                messages.success(request, f"База данных (схема) «{schema_name}» успешно создана!")
                return redirect("database_schemas", pk=pk)

            # ---------- PostgreSQL ----------
            with conn.cursor() as cursor:
                cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.schemata
                            WHERE schema_name = %s
                        );
                    """, (schema_name,))
                if cursor.fetchone()[0]:
                    messages.warning(request, f"Схема «{schema_name}» уже существует!")
                    return redirect("database_schemas_create", pk=pk)
                create_schema_query = sql.SQL("CREATE SCHEMA {};").format(
                    sql.Identifier(schema_name)
                )
                cursor.execute(create_schema_query)
            conn.commit()
            messages.success(request, f"Схема «{schema_name}» успешно создана!")
            return redirect("database_schemas", pk=pk)

        except Exception as e:
            try:
                if hasattr(conn, "rollback"):
                    conn.rollback()
            except Exception:
                pass
            messages.warning(request, f"Ошибка создания схемы: {e}")
        finally:
            close_connection(conn)
    return render(
        request,
        template_name="database_schemas_create.html",
        context={"project": project, "error_message": error_message},
    )


@login_required
def database_schema_delete(request, pk, schema_name: str):
    """Удаление схемы в базе данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas", args=[pk])
    if request.method != "POST":
        return redirect(next_url)

    connection, error_message = get_db_connection(project)
    if not connection:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)

    engine = get_engine(project)
    success = False

    try:
        if engine == "clickhouse":
            # В ClickHouse "схема" = база данных
            connection.command(f"DROP DATABASE `{schema_name}`")
            messages.success(request, f"База данных (схема) «{schema_name}» успешно удалена.")
            success = True
        else:
            # PostgreSQL
            with connection.cursor() as cursor:
                drop_stmt = sql.SQL("DROP SCHEMA {} CASCADE;").format(sql.Identifier(schema_name))
                cursor.execute(drop_stmt)
            connection.commit()
            messages.success(request, f"Схема «{schema_name}» успешно удалена.")
            success = True

    except Exception as e:
        if engine == "postgres" and hasattr(connection, "rollback"):
            connection.rollback()
        messages.warning(request, f"Ошибка удаления схемы «{schema_name}»: {str(e)}")
    finally:
        close_connection(connection)

    return redirect(next_url)


@login_required
def database_schema_edit(request, pk, schema_name: str):
    """Переименование схемы в базе данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas", args=[pk])
    if request.method != "POST":
        return redirect(next_url)
    new_name = (request.POST.get("new_schema_name") or "").strip()
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_name):
        messages.warning(request, "Недопустимое имя схемы. Разрешены латинские буквы, цифры и «_», первый символ — буква или «_».")
        return redirect(next_url)
    if new_name == schema_name:
        messages.info(request, "Имя схемы не изменилось.")
        return redirect(next_url)
    connection, error_message = get_db_connection(project)
    if not connection:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)
    engine = get_engine(project)
    success = False
    try:
        if engine == "clickhouse":
            messages.warning(request, "ClickHouse не поддерживает переименование базы данных (схемы).")
        else:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.schemata WHERE schema_name = %s
                    );
                """, (new_name,))
                exists = cursor.fetchone()[0]
                if exists:
                    messages.warning(request, f"Схема «{new_name}» уже существует.")
                    return redirect(next_url)
                alter_stmt = sql.SQL("ALTER SCHEMA {} RENAME TO {};").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(new_name)
                )
                cursor.execute(alter_stmt)
            connection.commit()
            messages.success(request, f"Схема «{schema_name}» переименована в «{new_name}».")
            success = True
    except Exception as e:
        if engine == "postgres" and hasattr(connection, "rollback"):
            connection.rollback()
        messages.warning(request, f"Ошибка переименования схемы: {str(e)}")
    finally:
        close_connection(connection)
    return redirect(next_url)


# TODO ТАБЛИЦЫ
@login_required
def database_schemas_tables(request, pk, schema_name):
    """Список таблиц в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    search_query = (request.GET.get("search") or "").strip()
    tables, error_message = [], None
    conn, error_message = get_db_connection(project)
    engine = get_engine(project)

    if conn:
        try:
            if engine == "clickhouse":
                rows = conn.query(
                    "SELECT name FROM system.tables WHERE database = %(db)s ORDER BY name",
                    parameters={"db": schema_name},
                ).result_rows
                tables = [r[0] for r in rows]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s
                        ORDER BY table_name
                    """, (schema_name,))
                    tables = [r[0] for r in cursor.fetchall()]
        finally:
            close_connection(conn)

    if search_query:
        q = search_query.lower()
        tables = [t for t in tables if q in t.lower()]

    return render(request,
                  template_name="database_schemas_tables.html",
                  context={
                      "project": project,
                      "schema_name": schema_name,
                      "tables": tables,
                      "error_message": error_message,
                      "search_query": search_query,
                      "engine": engine,
                  })


@login_required
def database_schemas_tables_create(request, pk, schema_name):
    """Создание таблицы в схеме базы данных с поддержкой PostgreSQL и ClickHouse"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    allowed_types = ALLOWED_TYPES
    engine = get_engine(project)

    if request.method == "POST":
        table_name = (request.POST.get("table_name") or "").strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            messages.error(
                request,
                "Название таблицы может содержать только латинские буквы, цифры и «_», "
                "и не может начинаться с цифры."
            )
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        suffixes = []
        for key in request.POST.keys():
            if key.startswith("column_name_"):
                suffixes.append(key[len("column_name_"):])
        suffixes = list(dict.fromkeys(suffixes))
        if not suffixes:
            messages.error(request, "Добавьте хотя бы один столбец.")
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        columns = []
        for suf in suffixes:
            name = (request.POST.get(f"column_name_{suf}") or "").strip()
            type_key = (request.POST.get(f"column_type_{suf}") or "").strip()
            comment = (request.POST.get(f"column_comment_{suf}") or "").strip()
            unique_flag = request.POST.get(f"column_unique_{suf}") == "on"
            if not name:
                continue
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
                messages.error(request, f"Недопустимое имя столбца: «{name}».")
                return render(request,
                              template_name="database_schemas_tables_create.html",
                              context={
                                  "project": project,
                                  "schema_name": schema_name,
                                  "engine": engine,
                              })
            if type_key not in allowed_types:
                messages.error(request, f"Недопустимый тип данных у столбца «{name}».")
                return render(request,
                              template_name="database_schemas_tables_create.html",
                              context={
                                  "project": project,
                                  "schema_name": schema_name,
                                  "engine": engine,
                              })
            columns.append({
                "name": name,
                "type_sql": allowed_types[type_key],
                "comment": comment,
                "unique": unique_flag,
            })

        if not columns:
            messages.error(request, "Нет валидных столбцов для создания.")
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        if any(c["name"].lower() == "id" for c in columns):
            messages.error(request, "Нельзя добавлять столбец с именем «id» — оно зарезервировано.")
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        seen, dupes = set(), []
        for c in columns:
            k = c["name"].lower()
            if k in seen:
                dupes.append(c["name"])
            seen.add(k)
        if dupes:
            messages.error(
                request,
                "Дублирующиеся имена столбцов: " + ", ".join(sorted(set(dupes))) +
                ". Имена столбцов должны быть уникальными."
            )
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        connection, error_message = get_db_connection(project)
        if not connection:
            messages.error(request, error_message or "Ошибка подключения к БД.")
            return render(request,
                          template_name="database_schemas_tables_create.html",
                          context={
                              "project": project,
                              "schema_name": schema_name,
                              "engine": engine,
                          })

        success = False
        try:
            if engine == "clickhouse":
                # Маппинг PostgreSQL-типов в ClickHouse
                ch_type_map = {
                    "INTEGER": "Int32",
                    "BIGINT": "Int64",
                    "TEXT": "String",
                    "VARCHAR(255)": "String",
                    "BOOLEAN": "UInt8",
                    "DATE": "Date",
                    "TIMESTAMP": "DateTime",
                    "FLOAT": "Float32",
                    "DOUBLE PRECISION": "Float64",
                }

                col_defs = []
                for col in columns:
                    ch_type = ch_type_map.get(col["type_sql"], "String")
                    col_line = f"`{col['name']}` {ch_type}"
                    # UNIQUE игнорируется — ClickHouse не поддерживает
                    col_defs.append(col_line)

                create_sql = f"""
                CREATE TABLE `{schema_name}`.`{table_name}`
                ({', '.join(col_defs)})
                ENGINE = MergeTree()
                ORDER BY tuple()
                """
                connection.command(create_sql)
                messages.success(request, f"Таблица «{schema_name}.{table_name}» успешно создана в ClickHouse.")
                success = True

            else:
                # PostgreSQL
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables 
                            WHERE table_schema = %s AND table_name = %s
                        );
                    """, (schema_name, table_name))
                    if cursor.fetchone()[0]:
                        messages.error(
                            request,
                            f"Таблица «{table_name}» уже существует в схеме «{schema_name}»."
                        )
                        return render(request,
                                      template_name="database_schemas_tables_create.html",
                                      context={
                                          "project": project,
                                          "schema_name": schema_name,
                                          "engine": engine,
                                      })

                    col_defs = []
                    for col in columns:
                        parts = [
                            sql.Identifier(col["name"]),
                            sql.SQL(" "),
                            sql.SQL(col["type_sql"]),
                        ]
                        if col["unique"]:
                            parts.append(sql.SQL(" UNIQUE"))
                        col_defs.append(sql.Composed(parts))

                    create_table_sql = sql.SQL(
                        "CREATE TABLE {}.{} (id SERIAL PRIMARY KEY, {});"
                    ).format(
                        sql.Identifier(schema_name),
                        sql.Identifier(table_name),
                        sql.SQL(", ").join(col_defs)
                    )
                    cursor.execute(create_table_sql)

                    for col in columns:
                        if col["comment"]:
                            cursor.execute(
                                sql.SQL("COMMENT ON COLUMN {} IS %s").format(
                                    sql.Identifier(schema_name, table_name, col["name"])
                                ),
                                (col["comment"],)
                            )
                connection.commit()
                messages.success(request, f"Таблица «{schema_name}.{table_name}» успешно создана.")
                success = True

        except Exception as e:
            if engine == "postgres" and hasattr(connection, "rollback"):
                connection.rollback()
            messages.error(request, f"Ошибка создания таблицы: {str(e)}")
        finally:
            close_connection(connection)

        if success:
            return redirect("database_schemas_tables", pk=pk, schema_name=schema_name)

    return render(
        request,
        template_name="database_schemas_tables_create.html",
        context={
            "project": project,
            "schema_name": schema_name,
            "engine": engine,
        }
    )


@login_required
def database_schemas_tables_delete(request, pk, schema_name: str, table_name: str):
    """Удаление таблицы в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas_tables", args=[pk, schema_name])
    if request.method != "POST":
        return redirect(next_url)
    conn, error_message = get_db_connection(project)
    if not conn:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)
    engine = get_engine(project)
    success = False
    try:
        if engine == "clickhouse":
            # ClickHouse: DROP TABLE `database`.`table`
            conn.command(f"DROP TABLE `{schema_name}`.`{table_name}`")
            messages.success(request, f"Таблица «{schema_name}.{table_name}» успешно удалена.")
            success = True
        else:
            # PostgreSQL
            with conn.cursor() as cur:
                drop_stmt = sql.SQL("DROP TABLE {} CASCADE;").format(
                    sql.Identifier(schema_name, table_name)
                )
                cur.execute(drop_stmt)
            conn.commit()
            messages.success(request, f"Таблица «{schema_name}.{table_name}» успешно удалена.")
            success = True
    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка удаления таблицы «{schema_name}.{table_name}»: {str(e)}")
    finally:
        close_connection(conn)
    return redirect(next_url)


@login_required
def database_schemas_tables_edit(request, pk, schema_name: str, table_name: str):
    """Переименование таблицы в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas_tables", args=[pk, schema_name])
    if request.method != "POST":
        return redirect(next_url)
    new_name = (request.POST.get("new_table_name") or "").strip()
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_name):
        messages.warning(request, "Недопустимое имя таблицы. Разрешены латинские буквы, цифры и «_», первый символ — буква или «_».")
        return redirect(next_url)
    if new_name == table_name:
        messages.info(request, "Имя таблицы не изменилось.")
        return redirect(next_url)
    conn, error_message = get_db_connection(project)
    if not conn:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)
    engine = get_engine(project)
    success = False
    try:
        if engine == "clickhouse":
            # ClickHouse не поддерживает RENAME TABLE для большинства движков
            messages.warning(request, "ClickHouse не поддерживает переименование таблиц. Операция невозможна.")
        else:
            # PostgreSQL
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    );
                """, (schema_name, new_name))
                exists = cur.fetchone()[0]
                if exists:
                    messages.warning(request, f"Таблица «{schema_name}.{new_name}» уже существует.")
                    return redirect(next_url)

                alter_stmt = sql.SQL("ALTER TABLE {} RENAME TO {};").format(
                    sql.Identifier(schema_name, table_name),
                    sql.Identifier(new_name)
                )
                cur.execute(alter_stmt)
            conn.commit()
            messages.success(request, f"Таблица «{schema_name}.{table_name}» переименована в «{schema_name}.{new_name}».")
            success = True
    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка переименования таблицы: {str(e)}")
    finally:
        close_connection(conn)
    return redirect(next_url)


# TODO КОЛОНКИ
@login_required
def database_schemas_tables_columns(request, pk, schema_name, table_name):
    """Колонки таблицы в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    search_query = (request.GET.get("search") or "").strip()
    columns, record_count, error_message, db_size_pretty = [], 0, None, "-"
    conn, error_message = get_db_connection(project)
    engine = get_engine(project)
    if conn:
        try:
            if get_engine(project) == "clickhouse":
                cols = conn.query("""
                    SELECT name, type, comment
                    FROM system.columns
                    WHERE database = %(db)s AND table = %(tbl)s
                    ORDER BY position
                """, parameters={"db": schema_name, "tbl": table_name}).result_rows
                columns = cols
                count_result = conn.query(f"SELECT count() FROM `{schema_name}`.`{table_name}`")
                record_count = count_result.result_rows[0][0] if count_result.result_rows else 0
                size_result = conn.query("""
                    SELECT sum(bytes) FROM system.parts
                    WHERE database = %(db)s AND table = %(tbl)s
                """, parameters={"db": schema_name, "tbl": table_name})
                size_bytes = size_result.result_rows[0][0] if size_result.result_rows else 0
                if size_bytes:
                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                        if size_bytes < 1024:
                            db_size_pretty = f"{size_bytes:.0f} {unit}"
                            break
                        size_bytes /= 1024
                else:
                    db_size_pretty = "0 B"
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT c.column_name, c.data_type, pgd.description
                        FROM information_schema.columns c
                        LEFT JOIN pg_catalog.pg_statio_all_tables st
                          ON st.schemaname = c.table_schema AND st.relname = c.table_name
                        LEFT JOIN pg_catalog.pg_description pgd
                          ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
                        WHERE c.table_schema = %s AND c.table_name = %s
                        ORDER BY c.ordinal_position
                    """, (schema_name, table_name))
                    columns = cursor.fetchall()
                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                    db_size_pretty = cursor.fetchone()[0]
                    cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
                    record_count = cursor.fetchone()[0]
        except Exception as e:
            error_message = f"Ошибка: {e}"
        finally:
            close_connection(conn)
    if search_query and columns:
        q = search_query.lower()

        def match(row):
            name = (row[0] or "").lower()
            dtype = (row[1] or "").lower()
            comment = (row[2] or "").lower() if len(row) > 2 and row[2] else ""
            return q in name or q in dtype or q in comment

        columns = [r for r in columns if match(r)]
    return render(request,
                  template_name="database_schemas_tables_columns.html",
                  context={
                      "project": project,
                      "schema_name": schema_name,
                      "table_name": table_name,
                      "columns": columns,
                      "record_count": record_count,
                      "error_message": error_message,
                      "search_query": search_query,
                      "db_size_pretty": db_size_pretty,
                      "engine": engine
                  })


@login_required
def database_schemas_column_delete(request, pk, schema_name: str, table_name: str, column_name: str):
    """Удаление колонки из таблицы"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas_tables_columns", args=[pk, schema_name, table_name])
    if request.method != "POST":
        return redirect(next_url)
    conn, error_message = get_db_connection(project)
    if not conn:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)
    engine = get_engine(project)
    success = False
    try:
        if engine == "clickhouse":
            result = conn.query("""
                    SELECT count() 
                    FROM system.columns 
                    WHERE database = %(db)s AND table = %(tbl)s AND name = %(col)s
                """, parameters={"db": schema_name, "tbl": table_name, "col": column_name})
            exists = result.result_rows[0][0] if result.result_rows else 0
            if not exists:
                messages.warning(request, f"Колонка «{column_name}» не найдена.")
                return redirect(next_url)
            conn.command(f"ALTER TABLE `{schema_name}`.`{table_name}` DROP COLUMN `{column_name}`")
            messages.success(request, f"Колонка «{schema_name}.{table_name}.{column_name}» успешно удалена.")
            success = True
        else:
            with conn.cursor() as cur:
                cur.execute("""
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema=%s AND table_name=%s AND column_name=%s
                        );
                    """, (schema_name, table_name, column_name))
                exists = cur.fetchone()[0]
                if not exists:
                    messages.warning(request, f"Колонка «{column_name}» не найдена.")
                    return redirect(next_url)
                drop_stmt = sql.SQL("ALTER TABLE {} DROP COLUMN {} CASCADE;").format(
                    sql.Identifier(schema_name, table_name),
                    sql.Identifier(column_name)
                )
                cur.execute(drop_stmt)
            conn.commit()
            messages.success(request, f"Колонка «{schema_name}.{table_name}.{column_name}» успешно удалена.")
            success = True
    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка удаления колонки «{schema_name}.{table_name}.{column_name}»: {str(e)}")
    finally:
        close_connection(conn)
    return redirect(next_url)


@login_required
def database_schemas_column_edit(request, pk, schema_name: str, table_name: str, column_name: str):
    """Переименование колонки и/или редактирование комментария"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas_tables_columns", args=[pk, schema_name, table_name])
    if request.method != "POST":
        return redirect(next_url)
    new_name = (request.POST.get("new_column_name") or "").strip()
    new_comment = (request.POST.get("new_column_comment") or "").strip()
    if new_name and not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", new_name):
        messages.warning(request, "Недопустимое имя колонки. Разрешены латинские буквы, цифры и «_», первый символ — буква или «_».")
        return redirect(next_url)
    if not new_name:
        new_name = column_name
    conn, error_message = get_db_connection(project)
    if not conn:
        messages.warning(request, error_message or "Ошибка подключения к БД.")
        return redirect(next_url)
    engine = get_engine(project)
    success = False
    try:
        if engine == "clickhouse":
            # ClickHouse не поддерживает ALTER COLUMN RENAME и COMMENT
            messages.warning(request, "ClickHouse не поддерживает переименование колонок и комментарии к ним.")
        else:
            # PostgreSQL
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.columns
                        WHERE table_schema=%s AND table_name=%s AND column_name=%s
                    );
                """, (schema_name, table_name, column_name))
                exists = cur.fetchone()[0]
                if not exists:
                    messages.warning(request, f"Колонка «{column_name}» не найдена.")
                    return redirect(next_url)

                if new_name != column_name:
                    cur.execute("""
                        SELECT EXISTS (
                            SELECT 1
                            FROM information_schema.columns
                            WHERE table_schema=%s AND table_name=%s AND column_name=%s
                        );
                    """, (schema_name, table_name, new_name))
                    if cur.fetchone()[0]:
                        messages.warning(request, f"Колонка «{new_name}» уже существует в «{schema_name}.{table_name}».")
                        return redirect(next_url)

                    rename_stmt = sql.SQL("ALTER TABLE {} RENAME COLUMN {} TO {};").format(
                        sql.Identifier(schema_name, table_name),
                        sql.Identifier(column_name),
                        sql.Identifier(new_name)
                    )
                    cur.execute(rename_stmt)

                comment_stmt = sql.SQL("COMMENT ON COLUMN {}.{}.{} IS %s;").format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name),
                    sql.Identifier(new_name)
                )
                cur.execute(comment_stmt, (new_comment or None,))

            conn.commit()
            success = True

            if new_name != column_name and new_comment:
                messages.success(request, f"Колонка переименована в «{new_name}» и обновлён комментарий.")
            elif new_name != column_name:
                messages.success(request, f"Колонка «{column_name}» переименована в «{new_name}».")
            elif new_comment or (request.POST.get("new_column_comment") is not None):
                messages.success(request, f"Комментарий к колонке «{new_name}» обновлён.")
            else:
                messages.info(request, "Изменений не требуется.")

    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка при редактировании колонки: {str(e)}")
    finally:
        close_connection(conn)

    return redirect(next_url)


@login_required
def database_schemas_table_data(request, pk, schema_name, table_name):
    """Данные в колонках таблицы базы данных (поддержка PostgreSQL и ClickHouse)"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    engine = get_engine(project)
    connection, error_message = get_db_connection(project)
    view_table_db = AppSettings.objects.first()
    page_size = view_table_db.view_table_db if view_table_db else 50

    if error_message:
        return render(request, 'error_page.html', {'error_message': error_message})

    columns = []
    rows = []
    record_count = 0
    db_size_pretty = "-"

    try:
        if engine == "clickhouse":
            # 1. Получаем список колонок
            col_result = connection.query("""
                SELECT name FROM system.columns
                WHERE database = %(db)s AND table = %(tbl)s
                ORDER BY position
            """, parameters={"db": schema_name, "tbl": table_name})
            columns = [r[0] for r in col_result.result_rows]

            # 2. Общее количество записей
            count_result = connection.query(f"SELECT count() FROM `{schema_name}`.`{table_name}`")
            record_count = count_result.result_rows[0][0] if count_result.result_rows else 0

            # 3. Размер базы (приблизительно)
            size_result = connection.query("""
                SELECT sum(bytes) FROM system.parts
                WHERE database = %(db)s AND table = %(tbl)s
            """, parameters={"db": schema_name, "tbl": table_name})
            size_bytes = size_result.result_rows[0][0] if size_result.result_rows else 0
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if size_bytes < 1024:
                    db_size_pretty = f"{size_bytes:.0f} {unit}"
                    break
                size_bytes /= 1024

            # 4. Пагинация и поиск
            page_number = request.GET.get('page', 1)
            try:
                page_number = int(page_number)
            except ValueError:
                page_number = 1
            offset = (page_number - 1) * page_size

            search_query = request.GET.get('search', '').strip()

            if search_query:
                # Поиск: LIKE по всем колонкам (только String-типы поддерживают LIKE)
                # Для простоты — ищем только в колонках типа String
                string_cols = []
                types_result = connection.query("""
                    SELECT name, type FROM system.columns
                    WHERE database = %(db)s AND table = %(tbl)s
                """, parameters={"db": schema_name, "tbl": table_name})
                for name, typ in types_result.result_rows:
                    if 'String' in typ or 'FixedString' in typ:
                        string_cols.append(name)

                if string_cols:
                    like_parts = " OR ".join([f"`{col}` LIKE %({col}_search)s" for col in string_cols])
                    params = {f"{col}_search": f"%{search_query}%" for col in string_cols}
                    params["limit"] = page_size
                    params["offset"] = offset
                    query = f"""
                        SELECT * FROM `{schema_name}`.`{table_name}`
                        WHERE {like_parts}
                        LIMIT %(limit)s OFFSET %(offset)s
                    """
                    data_result = connection.query(query, parameters=params)
                else:
                    # Нет текстовых колонок — возвращаем пусто
                    data_result = connection.query(
                        f"SELECT * FROM `{schema_name}`.`{table_name}` LIMIT 0"
                    )
            else:
                data_result = connection.query(f"""
                    SELECT * FROM `{schema_name}`.`{table_name}`
                    LIMIT {page_size} OFFSET {offset}
                """)

            rows = data_result.result_rows

        else:
            # PostgreSQL
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_schema = %s AND table_name = %s;
                """, (schema_name, table_name))
                columns = [col[0] for col in cursor.fetchall()]

                cursor.execute(sql.SQL('SELECT COUNT(*) FROM {}.{};').format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                ))
                record_count = cursor.fetchone()[0]

                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                db_size_pretty = cursor.fetchone()[0]

                page_number = request.GET.get('page', 1)
                try:
                    page_number = int(page_number)
                except ValueError:
                    page_number = 1
                offset = (page_number - 1) * page_size

                search_query = request.GET.get('search', '').strip()
                query_params = []

                if search_query:
                    search_conditions = " OR ".join([f'"{col}"::text ILIKE %s' for col in columns])
                    sql_query = sql.SQL(
                        'SELECT * FROM {}.{} WHERE ' + search_conditions + ' LIMIT %s OFFSET %s;'
                    ).format(sql.Identifier(schema_name), sql.Identifier(table_name))
                    query_params = [f"%{search_query}%"] * len(columns) + [page_size, offset]
                else:
                    sql_query = sql.SQL('SELECT * FROM {}.{} LIMIT %s OFFSET %s;').format(
                        sql.Identifier(schema_name), sql.Identifier(table_name)
                    )
                    query_params = [page_size, offset]

                cursor.execute(sql_query, query_params)
                rows = cursor.fetchall()

        # Пагинация (для обеих СУБД)
        paginator = Paginator(range(record_count), page_size)
        try:
            page_obj = paginator.page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.page(1)

        return render(
            request,
            template_name='database_schemas_table_data.html',
            context={
                'project': project,
                'schema_name': schema_name,
                'table_name': table_name,
                'columns': columns,
                'rows': rows,
                'record_count': record_count,
                'records_on_page': len(rows),
                'search_query': request.GET.get('search', '').strip(),
                'db_size_pretty': db_size_pretty,
                'page_obj': page_obj,
            }
        )

    except Exception as e:
        error_message = f"Ошибка загрузки данных: {str(e)}"
        return render(request, 'error_page.html', {'error_message': error_message})
    finally:
        close_connection(connection)


@login_required
def database_schemas_table_add_columns(request, pk, schema_name: str, table_name: str):
    """Добавление полей в таблицу базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    engine = get_engine(project)
    next_url = request.POST.get("next") or reverse(
        "database_schemas_tables_columns", args=[pk, schema_name, table_name]
    )
    if request.method != "POST":
        return render(
            request,
            template_name="database_schemas_table_add_columns.html",
            context={
                "project": project,
                "schema_name": schema_name,
                "table_name": table_name,
                "engine": engine,
            },
        )
    allowed_types = ALLOWED_TYPES
    row_indices = request.POST.getlist("row_indices[]")
    if not row_indices:
        messages.warning(request, "Добавьте хотя бы один столбец.")
        return redirect(next_url)
    cols = []
    names_seen_lower = set()
    dups = set()
    for idx in row_indices:
        name = (request.POST.get(f"col_name_{idx}") or "").strip()
        tkey = (request.POST.get(f"col_type_{idx}") or "").strip()
        comment = (request.POST.get(f"col_comment_{idx}") or "").strip()
        unique = request.POST.get(f"col_unique_{idx}") == "on"
        if not name:
            continue
        if not IDENT_RE.match(name):
            messages.warning(request, f"Недопустимое имя столбца: «{name}».")
            return redirect(next_url)
        if tkey not in allowed_types:
            messages.warning(request, f"Недопустимый тип у столбца «{name}».")
            return redirect(next_url)
        low = name.lower()
        if low in names_seen_lower:
            dups.add(name)
        names_seen_lower.add(low)
        cols.append({
            "name": name,
            "type_sql": allowed_types[tkey],
            "comment": comment,
            "unique": unique,
        })
    if dups:
        messages.warning(
            request,
            f"Дублирующиеся имена столбцов: {', '.join(sorted(dups))}. Имена столбцов должны быть уникальными.",
        )
        return redirect(next_url)
    if not cols:
        messages.warning(request, "Нет валидных столбцов для добавления.")
        return redirect(next_url)
    conn, err = get_db_connection(project)
    if not conn:
        messages.warning(request, err or "Ошибка подключения к БД.")
        return redirect(next_url)
    success = False
    try:
        if engine == "clickhouse":
            ch_type_map = {
                "INTEGER": "Int32",
                "BIGINT": "Int64",
                "TEXT": "String",
                "VARCHAR(255)": "String",
                "BOOLEAN": "UInt8",
                "DATE": "Date",
                "TIMESTAMP": "DateTime",
                "FLOAT": "Float32",
                "DOUBLE PRECISION": "Float64",
            }
            result = conn.query("""
                SELECT count() FROM system.tables
                WHERE database = %(db)s AND name = %(tbl)s
            """, parameters={"db": schema_name, "tbl": table_name})
            exists = result.result_rows[0][0] if result.result_rows else 0
            if not exists:
                messages.warning(request, "Таблица не найдена.")
                return redirect(next_url)
            for c in cols:
                ch_type = ch_type_map.get(c["type_sql"], "String")
                conn.command(f"ALTER TABLE `{schema_name}`.`{table_name}` ADD COLUMN `{c['name']}` {ch_type}")
            messages.success(request, f"Столбцы успешно добавлены в «{schema_name}.{table_name}».")
            success = True
        else:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = %s AND table_name = %s
                    );
                """, (schema_name, table_name))
                exists = cur.fetchone()[0]
                if not exists:
                    messages.warning(request, "Таблица не найдена.")
                    return redirect(next_url)
                for c in cols:
                    add_stmt = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                        sql.Identifier(schema_name, table_name),
                        sql.Identifier(c["name"]),
                        sql.SQL(c["type_sql"]),
                    )
                    if c["unique"]:
                        add_stmt = sql.Composed([add_stmt, sql.SQL(" UNIQUE")])
                    cur.execute(add_stmt)
                    if c["comment"]:
                        cur.execute(
                            sql.SQL("COMMENT ON COLUMN {} IS %s").format(
                                sql.Identifier(schema_name, table_name, c["name"])
                            ),
                            (c["comment"],),
                        )
            conn.commit()
            messages.success(request, f"Столбцы успешно добавлены в «{schema_name}.{table_name}».")
            success = True
    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка добавления столбцов: {str(e)}")
    finally:
        close_connection(conn)
    return redirect(next_url)


@login_required
def database_schemas_table_clear(request, pk, schema_name: str, table_name: str):
    """Полная очистка таблицы с поддержкой PostgreSQL и ClickHouse"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    engine = get_engine(project)
    next_url = request.POST.get("next") or reverse(
        "database_schemas_tables_columns", args=[pk, schema_name, table_name]
    )

    if request.method != "POST":
        return redirect(next_url)

    restart_identity = request.POST.get("restart_identity") == "on"

    conn, err = get_db_connection(project)
    if not conn:
        messages.warning(request, err or "Ошибка подключения к БД.")
        return redirect(next_url)

    success = False
    before_cnt = 0

    try:
        if engine == "clickhouse":
            # 1. Получаем количество строк ДО удаления
            count_result = conn.query(f"SELECT count() FROM `{schema_name}`.`{table_name}`")
            before_cnt = count_result.result_rows[0][0] if count_result.result_rows else 0

            # 2. Очистка таблицы
            # В новых версиях ClickHouse (>=22.8) поддерживается TRUNCATE
            try:
                conn.command(f"TRUNCATE TABLE `{schema_name}`.`{table_name}`")
            except Exception:
                # Если TRUNCATE не поддерживается — используем ALTER DELETE (медленнее)
                conn.command(f"ALTER TABLE `{schema_name}`.`{table_name}` DELETE WHERE 1=1")

            messages.success(
                request,
                f"Таблица «{schema_name}.{table_name}» очищена (удалено {before_cnt} строк)."
            )
            success = True

        else:
            # PostgreSQL
            with conn.cursor() as cur:
                cur.execute(sql.SQL('SELECT COUNT(*) FROM {}.{};').format(
                    sql.Identifier(schema_name), sql.Identifier(table_name)
                ))
                before_cnt = cur.fetchone()[0]

                truncate_sql = sql.SQL("TRUNCATE TABLE {} {}").format(
                    sql.Identifier(schema_name, table_name),
                    sql.SQL("RESTART IDENTITY") if restart_identity else sql.SQL("")
                )
                cur.execute(truncate_sql)
            conn.commit()

            if restart_identity:
                messages.success(
                    request,
                    f"Таблица «{schema_name}.{table_name}» очищена "
                    f"(удалено {before_cnt} строк), автоинкремент сброшен."
                )
            else:
                messages.success(
                    request,
                    f"Таблица «{schema_name}.{table_name}» очищена (удалено {before_cnt} строк)."
                )
            success = True

    except Exception as e:
        if engine == "postgres" and hasattr(conn, "rollback"):
            conn.rollback()
        messages.warning(request, f"Ошибка очистки таблицы: {str(e)}")
    finally:
        close_connection(conn)

    return redirect(next_url)


# TODO ГЕНЕРАТОР
@login_required
def generate_fake_data(request, pk, schema_name, table_name):
    project = get_object_or_404(DataBaseUser, pk=pk)
    fake = Faker('ru_RU')
    Faker.seed()

    error_message = None
    inserted_rows = 0
    record_count = 0
    retry_attempts = 200
    db_size_pretty = "-"
    column_data = []
    engine = get_engine(project)

    conn, error_message = get_db_connection(project)
    if conn:
        try:
            if engine == "clickhouse":
                cols_result = conn.query("""
                    SELECT name, type
                    FROM system.columns
                    WHERE database = %(db)s AND table = %(tbl)s
                    ORDER BY position
                """, parameters={"db": schema_name, "tbl": table_name})
                cols = cols_result.result_rows

                column_data = []
                for col_name, db_type in cols:
                    col_type_lower = db_type.lower()
                    if 'int' in col_type_lower and 'uint8' not in col_type_lower:
                        choices = ['Целое число', 'Число (маленькое)', 'Число (большое)', 'Возраст', 'Рейтинг (1-5)', 'Оценка (1-10)']
                    elif 'uint8' in col_type_lower:
                        choices = ['True/False']
                    elif 'string' in col_type_lower or 'fixedstring' in col_type_lower:
                        choices = ALL_CHOICES
                    elif 'date' in col_type_lower and 'datetime' not in col_type_lower:
                        choices = ['Дата', 'Дата рождения', 'Дата в прошлом', 'Дата в будущем']
                    elif 'datetime' in col_type_lower:
                        choices = ['Дата и время', 'Дата в прошлом', 'Дата в будущем']
                    elif 'float' in col_type_lower:
                        choices = ['Число с запятой', 'Широта', 'Долгота', 'Метрика']
                    else:
                        choices = ['Произвольное значение']
                    column_data.append({
                        "name": col_name,
                        "type": db_type,
                        "choices": choices
                    })

                count_result = conn.query(f"SELECT count() FROM `{schema_name}`.`{table_name}`")
                record_count = count_result.result_rows[0][0] if count_result.result_rows else 0

                size_result = conn.query("""
                    SELECT sum(bytes) FROM system.parts
                    WHERE database = %(db)s AND table = %(tbl)s
                """, parameters={"db": schema_name, "tbl": table_name})
                size_bytes = size_result.result_rows[0][0] if size_result.result_rows else 0
                for unit in ["B", "KB", "MB", "GB", "TB"]:
                    if size_bytes < 1024:
                        db_size_pretty = f"{size_bytes:.0f} {unit}"
                        break
                    size_bytes /= 1024

            else:
                with conn.cursor() as cur:
                    cur.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
                    record_count = cur.fetchone()[0]

                    cur.execute("""
                        SELECT column_name, data_type
                        FROM information_schema.columns
                        WHERE table_schema = %s AND table_name = %s
                        ORDER BY ordinal_position;
                    """, (schema_name, table_name))
                    cols = cur.fetchall()

                    column_data = []
                    for col_name, db_type in cols:
                        choices = choices_list.get(db_type.lower(), ['Произвольное значение'])
                        column_data.append({
                            "name": col_name,
                            "type": db_type,
                            "choices": choices
                        })

                    cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                    db_size_pretty = cur.fetchone()[0]

        except Exception as e:
            error_message = f"Ошибка получения структуры: {str(e)}"
        finally:
            close_connection(conn)

    # === Вставка данных ===
    if request.method == 'POST' and not error_message:
        try:
            num_records = int(request.POST.get('num_records', 10))
        except (ValueError, TypeError):
            num_records = 10
        num_records = max(1, min(num_records, 10000))

        conn2, err2 = get_db_connection(project)
        if not conn2:
            error_message = err2 or "Не удалось подключиться к БД."
        else:
            try:
                if engine == "clickhouse":
                    cols_result = conn2.query("""
                        SELECT name, type FROM system.columns
                        WHERE database = %(db)s AND table = %(tbl)s
                        ORDER BY position
                    """, parameters={"db": schema_name, "tbl": table_name})
                    cols_for_insert = [{"name": r[0], "type": r[1]} for r in cols_result.result_rows]

                    if not cols_for_insert:
                        error_message = "Таблица пуста или не существует."
                    else:
                        rows_to_insert = []
                        for _ in range(num_records):
                            row = []
                            for col in cols_for_insert:
                                value = generate_fake_value(
                                    col["name"],
                                    request.POST.get(f'column_{col["name"]}', 'Произвольное значение'),
                                    fake
                                )
                                # Убедимся, что дата/время — это объекты, а не строки
                                if 'datetime' in col["type"].lower():
                                    if isinstance(value, str):
                                        from datetime import datetime
                                        try:
                                            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
                                        except:
                                            value = fake.date_time()
                                elif 'date' in col["type"].lower() and 'datetime' not in col["type"].lower():
                                    if isinstance(value, str):
                                        from datetime import date
                                        try:
                                            value = date.fromisoformat(value)
                                        except:
                                            value = fake.date_object()

                                # Boolean → UInt8
                                if 'uint8' in col["type"].lower() and isinstance(value, bool):
                                    value = int(value)

                                row.append(value)
                            rows_to_insert.append(row)

                        col_names = [col["name"] for col in cols_for_insert]
                        conn2.insert(
                            table=f"`{schema_name}`.`{table_name}`",
                            data=rows_to_insert,
                            column_names=col_names
                        )
                        inserted_rows = num_records

                        count_result = conn2.query(f"SELECT count() FROM `{schema_name}`.`{table_name}`")
                        record_count = count_result.result_rows[0][0] if count_result.result_rows else 0

                        size_result = conn2.query("""
                            SELECT sum(bytes) FROM system.parts
                            WHERE database = %(db)s AND table = %(tbl)s
                        """, parameters={"db": schema_name, "tbl": table_name})
                        size_bytes = size_result.result_rows[0][0] if size_result.result_rows else 0
                        for unit in ["B", "KB", "MB", "GB", "TB"]:
                            if size_bytes < 1024:
                                db_size_pretty = f"{size_bytes:.0f} {unit}"
                                break
                            size_bytes /= 1024

                else:
                    with conn2.cursor() as cur:
                        cur.execute("""
                            SELECT column_name, data_type
                            FROM information_schema.columns
                            WHERE table_schema = %s AND table_name = %s
                            ORDER BY ordinal_position;
                        """, (schema_name, table_name))
                        cols = cur.fetchall()
                        cols_for_insert = [{"name": c[0], "type": c[1]} for c in cols]

                        if not cols_for_insert:
                            error_message = "Таблица пуста или не существует."
                        else:
                            column_names_sql = ', '.join([f'"{c["name"]}"' for c in cols_for_insert])
                            placeholders = ', '.join(['%s'] * len(cols_for_insert))
                            insert_sql = f'INSERT INTO "{schema_name}"."{table_name}" ({column_names_sql}) VALUES ({placeholders})'

                            for _ in range(num_records):
                                attempt = 0
                                while attempt < retry_attempts:
                                    values = [
                                        generate_fake_value(
                                            col["name"],
                                            request.POST.get(f'column_{col["name"]}', 'Произвольное значение'),
                                            fake
                                        )
                                        for col in cols_for_insert
                                    ]
                                    try:
                                        cur.execute(insert_sql, values)
                                        inserted_rows += 1
                                        break
                                    except psycopg2.IntegrityError:
                                        conn2.rollback()
                                        attempt += 1
                                        if attempt >= retry_attempts:
                                            raise
                            conn2.commit()

                            cur.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
                            record_count = cur.fetchone()[0]
                            cur.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
                            db_size_pretty = cur.fetchone()[0]

            except Exception as e:
                error_message = f"Ошибка вставки: {str(e)}"
            finally:
                close_connection(conn2)

    return render(request, 'generate_fake_data.html', {
        'project': project,
        'schema_name': schema_name,
        'table_name': table_name,
        'column_data': column_data,
        'inserted_rows': inserted_rows,
        'record_count': record_count,
        'db_size_pretty': db_size_pretty,
        'error_message': error_message,
        'engine': engine,
    })


# TODO CSV
@login_required
def generate_csv(request):
    if request.method == 'POST':
        fields = request.POST.getlist('fields')
        if not fields:
            return HttpResponseBadRequest('Не переданы поля (fields).')

        try:
            num_records = int(request.POST.get('num_records', 10))
        except (ValueError, TypeError):
            num_records = 10
        num_records = max(1, min(num_records, 10_000_000))  # Ограничение

        fake = Faker('ru_RU')
        Faker.seed()  # Для случайности

        def row_iter():
            buf = io.StringIO()
            writer = csv.writer(buf)

            # Заголовок
            writer.writerow(fields)
            yield buf.getvalue().encode('utf-8')
            buf.seek(0);
            buf.truncate()

            # Данные
            for _ in range(num_records):
                row = [generate_fake_value(col, col, fake) for col in fields]
                writer.writerow(row)
                yield buf.getvalue().encode('utf-8')
                buf.seek(0);
                buf.truncate()

        ts = timezone.now().strftime('%Y%m%d_%H%M%S')
        filename = f'fake_data_{ts}.csv'

        response = StreamingHttpResponse(row_iter(), content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    return render(request, 'generate_csv.html', {'choices_list': ALL_CHOICES})
