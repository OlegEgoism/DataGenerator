import re

import psycopg2
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse
from psycopg2 import sql

from data_generator.db_connection import get_db_connection
from data_generator.forms import CustomUserCreationForm, CustomUserForm, DataBaseUserForm
from data_generator.models import DataBaseUser, AppSettings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


def home(request):
    """Главная"""
    return render(request,
                  template_name='home.html'
                  )


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


# TODO БАЗА ДАННЫХ
@login_required
def database_schemas(request, pk):
    """Схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    schemas, error_message = [], None
    connection, error_message = get_db_connection(project)
    if connection:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema')
                ORDER BY schema_name;
            """)
            schemas = [row[0] for row in cursor.fetchall()]
        connection.close()
    return render(request,
                  template_name='database_schemas.html',
                  context={
                      'project': project,
                      'schemas': schemas,
                      'error_message': error_message}
                  )


@login_required
def database_schemas_create(request, pk):
    """Создание схемы базы данных"""
    project = get_object_or_404(DataBaseUser, pk=pk)
    error_message = None
    if request.method == "POST":
        schema_name = request.POST.get("schema_name").strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", schema_name):
            messages.warning(request, "Название схемы может содержать только буквы, цифры и '_', но не начинаться с цифры.")
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
