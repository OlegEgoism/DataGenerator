import re
import psycopg2
from django.contrib.auth import logout
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.urls import reverse
from psycopg2 import sql
from data_generator.db_connection import get_db_connection
from data_generator.forms import CustomUserCreationForm, CustomUserForm, DataBaseUserForm
from data_generator.models import DataBaseUser, AppSettings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

IDENT_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
ALLOWED_TYPES = {
        "SMALLINT": "SMALLINT",
        "INTEGER": "INTEGER",
        "BIGINT": "BIGINT",

        "SERIAL": "SERIAL",
        "BIGSERIAL": "BIGSERIAL",

        "REAL": "REAL",
        "DOUBLE PRECISION": "DOUBLE PRECISION",
        "FLOAT": "DOUBLE PRECISION",
        "NUMERIC": "NUMERIC",

        "BOOLEAN": "BOOLEAN",

        "CHAR(1)": "CHAR(1)",
        "VARCHAR(255)": "VARCHAR(255)",
        "TEXT": "TEXT",

        "DATE": "DATE",
        "TIME": "TIME",
        "TIMESTAMP": "TIMESTAMP",
        "TIMESTAMPTZ": "TIMESTAMPTZ",

        "UUID": "UUID",
        "JSONB": "JSONB",
        "BYTEA": "BYTEA",
    }

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
                try:
                    connection = psycopg2.connect(
                        dbname=db_obj.db_name,
                        user=db_obj.db_user,
                        password=db_obj.db_password,
                        host=db_obj.db_host,
                        port=db_obj.db_port,
                        connect_timeout=connect_timeout,
                    )
                    connection.close()
                    messages.success(request, f"Успешное подключение к базе данных '{db_obj.db_name}'.")
                except psycopg2.OperationalError:
                    messages.warning(request, "Ошибка подключения! Проверьте настройки подключения.")
                except Exception as e:
                    messages.warning(request, f"Ошибка подключения: {str(e)}")
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
    """Синхронизация проекта"""
    project = get_object_or_404(DataBaseUser, pk=pk, user=request.user)
    next_url = request.POST.get("next") or reverse("projects")
    if request.method != "POST":
        return redirect(next_url)
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    try:
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
    except psycopg2.OperationalError:
        messages.warning(request, "Ошибка подключения! Проверьте настройки подключения.")
    except Exception as e:
        messages.warning(request, f"Ошибка подключения: {str(e)}")
    return redirect(next_url)


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


# TODO СХЕМЫ
@login_required
def database_schemas(request, pk):
    """Схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    search_query = request.GET.get("search", "").strip()
    schemas, error_message = [], None
    connection, error_message = get_db_connection(project)
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT schema_name
                    FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema')
                    ORDER BY schema_name;
                """)
                schemas = [row[0] for row in cursor.fetchall()]
        finally:
            connection.close()
    if search_query:
        q = search_query.lower()
        schemas = [s for s in schemas if q in s.lower()]
    return render(request,
                  template_name='database_schemas.html',
                  context={
                      'project': project,
                      'schemas': schemas,
                      'error_message': error_message,
                      'search_query': search_query}
                  )


@login_required
def database_schemas_create(request, pk):
    """Создание схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    if request.method == "POST":
        schema_name = request.POST.get("schema_name").strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            messages.warning(request, "Название схемы может содержать только буквы, цифры и символ '_', но не начинаться с цифры.")
            return redirect("database_schemas_create", pk=pk)
        connection, error_message = get_db_connection(project)
        if connection:
            try:
                with connection.cursor() as cursor:
                    check_schema_query = sql.SQL("""
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.schemata 
                            WHERE schema_name = %s
                        );
                    """)
                    cursor.execute(check_schema_query, (schema_name,))
                    schema_exists = cursor.fetchone()[0]
                    if schema_exists:
                        messages.warning(request, f"Схема '{schema_name}' уже существует!")
                        return redirect("database_schemas_create", pk=pk)
                    create_schema_query = sql.SQL("CREATE SCHEMA {};").format(
                        sql.Identifier(schema_name)
                    )
                    cursor.execute(create_schema_query)
                    connection.commit()
                messages.success(request, f"Схема '{schema_name}' успешно создана!")
                return redirect("database_schemas", pk=pk)
            except Exception as e:
                error_message = f"Ошибка создания схемы: {str(e)}"
            finally:
                connection.close()
    return render(request,
                  template_name="database_schemas_create.html",
                  context={
                      'project': project,
                      'error_message': error_message}
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
    try:
        with connection.cursor() as cursor:
            drop_stmt = sql.SQL("DROP SCHEMA {} CASCADE;").format(sql.Identifier(schema_name))
            cursor.execute(drop_stmt)
        connection.commit()
        messages.success(request, f"Схема «{schema_name}» успешно удалена.")
    except Exception as e:
        connection.rollback()
        messages.warning(request, f"Ошибка удаления схемы «{schema_name}»: {str(e)}")
    finally:
        connection.close()
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
    try:
        with connection.cursor() as cursor:
            # проверим, что новой схемы не существует
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
    except Exception as e:
        connection.rollback()
        messages.warning(request, f"Ошибка переименования схемы: {str(e)}")
    finally:
        connection.close()

    return redirect(next_url)


# TODO ТАБЛИЦЫ
@login_required
def database_schemas_tables(request, pk, schema_name):
    """Список таблиц в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    search_query = request.GET.get("search", "").strip()
    tables, error_message = [], None
    connection, error_message = get_db_connection(project)
    if connection:
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    ORDER BY table_name;
                """, (schema_name,))
                tables = [row[0] for row in cursor.fetchall()]
        finally:
            connection.close()
    if search_query:
        q = search_query.lower()
        tables = [t for t in tables if q in t.lower()]
    return render(request,
                  template_name='database_schemas_tables.html',
                  context={
                      'project': project,
                      'schema_name': schema_name,
                      'tables': tables,
                      'error_message': error_message,
                      'search_query': search_query}
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
    try:
        with conn.cursor() as cur:
            drop_stmt = sql.SQL("DROP TABLE {} CASCADE;").format(sql.Identifier(schema_name, table_name))
            cur.execute(drop_stmt)
        conn.commit()
        messages.success(request, f"Таблица «{schema_name}.{table_name}» успешно удалена.")
    except Exception as e:
        conn.rollback()
        messages.warning(request, f"Ошибка удаления таблицы «{schema_name}.{table_name}»: {str(e)}")
    finally:
        conn.close()
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
    try:
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
    except Exception as e:
        conn.rollback()
        messages.warning(request, f"Ошибка переименования таблицы: {str(e)}")
    finally:
        conn.close()
    return redirect(next_url)


# TODO КОЛОНКИ
@login_required
def database_schemas_tables_columns(request, pk, schema_name, table_name):
    """Колонки таблицы в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    columns, record_count, error_message = [], 0, None
    connection, error_message = get_db_connection(project)
    if connection:
        try:
            with connection.cursor() as cursor:
                check_table_query = sql.SQL("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """)
                cursor.execute(check_table_query, (schema_name, table_name))
                table_exists = cursor.fetchone()[0]
                if not table_exists:
                    error_message = f"Ошибка: Таблица '{table_name}' в схеме '{schema_name}' не существует!"
                    return render(request,
                                  template_name="database_schemas_tables_columns.html",
                                  context={
                                      "project": project,
                                      "schema_name": schema_name,
                                      "table_name": table_name,
                                      "columns": [],
                                      "record_count": 0,
                                      "error_message": error_message}
                                  )
                query = sql.SQL("""
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_schema = %s 
                      AND table_name = %s;
                """)
                cursor.execute(query, (schema_name, table_name))
                columns = cursor.fetchall()
                count_query = sql.SQL('SELECT COUNT(*) FROM {}.{};').format(
                    sql.Identifier(schema_name),
                    sql.Identifier(table_name)
                )
                cursor.execute(count_query)
                record_count = cursor.fetchone()[0]
        except Exception as e:
            error_message = f"Ошибка: {str(e)}"
        finally:
            connection.close()
    return render(request,
                  template_name="database_schemas_tables_columns.html",
                  context={
                      "project": project,
                      "schema_name": schema_name,
                      "table_name": table_name,
                      "columns": columns,
                      "record_count": record_count,
                      "error_message": error_message}
                  )


@login_required
def database_schemas_table_data(request, pk, schema_name, table_name):
    """Данные в колонках таблицы схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    connection, error_message = get_db_connection(project)
    view_table_db = AppSettings.objects.first()
    if error_message:
        return render(request, 'error_page.html', {'error_message': error_message})
    cursor = connection.cursor()
    cursor.execute(f"""
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s;
    """, (schema_name, table_name))
    columns = [col[0] for col in cursor.fetchall()]
    cursor.execute(f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}";')
    record_count = cursor.fetchone()[0]
    page_size = view_table_db.view_table_db if view_table_db else 50
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
        sql_query = f'SELECT * FROM "{schema_name}"."{table_name}" WHERE {search_conditions} LIMIT {page_size} OFFSET {offset};'
        query_params = [f"%{search_query}%"] * len(columns)
    else:
        sql_query = f'SELECT * FROM "{schema_name}"."{table_name}" LIMIT {page_size} OFFSET {offset};'
    cursor.execute(sql_query, query_params)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    paginator = Paginator(range(record_count), page_size)
    try:
        page_obj = paginator.page(page_number)
    except (EmptyPage, PageNotAnInteger):
        page_obj = paginator.page(1)
    return render(request,
                  template_name='database_schemas_table_data.html',
                  context={
                      'project': project,
                      'schema_name': schema_name,
                      'table_name': table_name,
                      'columns': columns,
                      'page_obj': page_obj,
                      'rows': rows,  #
                      'record_count': record_count,
                      'records_on_page': len(rows),
                      'search_query': search_query}
                  )


@login_required
def database_schemas_tables_create(request, pk, schema_name):
    """Создание таблицы в схеме базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    allowed_types = ALLOWED_TYPES
    if request.method == "POST":
        table_name = (request.POST.get("table_name") or "").strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", table_name):
            messages.error(request, "Название таблицы может содержать только латинские буквы, цифры и «_», и не может начинаться с цифры.")
            return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
        row_indices = request.POST.getlist("row_indices[]")
        if not row_indices:
            messages.error(request, "Добавьте хотя бы один столбец.")
            return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
        columns = []
        for idx_str in row_indices:
            name = (request.POST.get(f"column_name_{idx_str}") or "").strip()
            type_key = (request.POST.get(f"column_type_{idx_str}") or "").strip()
            comment = (request.POST.get(f"column_comment_{idx_str}") or "").strip()
            unique_flag = request.POST.get(f"column_unique_{idx_str}") == "on"
            if not name:
                continue
            if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
                messages.error(request, f"Недопустимое имя столбца: «{name}».")
                return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
            if type_key not in allowed_types:
                messages.error(request, f"Недопустимый тип данных у столбца «{name}».")
                return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
            columns.append({
                "name": name,
                "type_sql": allowed_types[type_key],
                "comment": comment,
                "unique": unique_flag,
            })

        if not columns:
            messages.error(request, "Нет валидных столбцов для создания.")
            return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
        connection, error_message = get_db_connection(project)
        if not connection:
            messages.error(request, error_message or "Ошибка подключения к БД.")
            return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = %s
                    );
                """, (schema_name, table_name))
                table_exists = cursor.fetchone()[0]
                if table_exists:
                    messages.error(request, f"Таблица «{table_name}» уже существует в схеме «{schema_name}».")
                    return render(request, "database_schemas_tables_create.html", {"project": project, "schema_name": schema_name})
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
            return redirect("database_schemas_tables", pk=pk, schema_name=schema_name)
        except Exception as e:
            connection.rollback()
            messages.error(request, f"Ошибка создания таблицы: {str(e)}")
        finally:
            connection.close()
    return render(
        request,
        template_name="database_schemas_tables_create.html",
        context={
            "project": project,
            "schema_name": schema_name,
            "error_message": error_message
        }
    )


@login_required
def database_schemas_table_add_columns(request, pk, schema_name: str, table_name: str):
    """Добавление полей в таблицу базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    next_url = request.POST.get("next") or reverse("database_schemas_tables_columns", args=[pk, schema_name, table_name])

    if request.method != "POST":
        return redirect(next_url)
    allowed_types = ALLOWED_TYPES
    row_indices = request.POST.getlist("row_indices[]")
    if not row_indices:
        messages.warning(request, "Добавьте хотя бы один столбец.")
        return redirect(next_url)

    cols = []
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

        cols.append({
            "name": name,
            "type_sql": allowed_types[tkey],
            "comment": comment,
            "unique": unique,
        })

    if not cols:
        messages.warning(request, "Нет валидных столбцов для добавления.")
        return redirect(next_url)

    conn, err = get_db_connection(project)
    if not conn:
        messages.warning(request, err or "Ошибка подключения к БД.")
        return redirect(next_url)

    try:
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

            # Добавляем по одному столбцу (чтобы легче обрабатывать возможные комментарии)
            for c in cols:
                # ALTER TABLE ... ADD COLUMN name type [UNIQUE];
                add_stmt = sql.SQL("ALTER TABLE {} ADD COLUMN {} {}").format(
                    sql.Identifier(schema_name, table_name),
                    sql.Identifier(c["name"]),
                    sql.SQL(c["type_sql"])
                )
                if c["unique"]:
                    add_stmt = sql.Composed([add_stmt, sql.SQL(" UNIQUE")])

                add_stmt = sql.Composed([add_stmt, sql.SQL(";")])
                cur.execute(add_stmt)

                if c["comment"]:
                    cur.execute(
                        sql.SQL("COMMENT ON COLUMN {} IS %s").format(
                            sql.Identifier(schema_name, table_name, c["name"])
                        ),
                        (c["comment"],)
                    )

        conn.commit()
        messages.success(request, f"Столбцы успешно добавлены в «{schema_name}.{table_name}».")
    except Exception as e:
        conn.rollback()
        messages.warning(request, f"Ошибка добавления столбцов: {str(e)}")
    finally:
        conn.close()

    return redirect(next_url)
