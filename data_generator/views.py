import psycopg2
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.urls import reverse

from data_generator.forms import CustomUserCreationForm, CustomUserForm, DataBaseUserForm
from data_generator.models import DataBaseUser, AppSettings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


def home(request):
    """Главная"""
    return render(request,
                  template_name='home.html')


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
                  context={"form": form})


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
                      'search_query': search_query})


@login_required
def profile_edit(request):
    """Редактирование профиля"""
    user = request.user
    if request.method == 'POST':
        form = CustomUserForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Профиль успешно обновлен.")
            return redirect('profile')
        else:
            messages.error(request, "Ошибка при обновлении профиля. Проверьте введенные данные.")
    else:
        form = CustomUserForm(instance=user)
    return render(request,
                  template_name='profile_edit.html',
                  context={'user': user,
                           'form': form})


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
                      "search_query": search_query})


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
def projects_edit(request, pk):
    """Редактирование проекта"""
    app_settings = AppSettings.objects.first()
    connect_timeout = app_settings.connect_timeout_db if app_settings else 5
    database = get_object_or_404(DataBaseUser, pk=pk)
    if request.method == 'POST':
        form = DataBaseUserForm(request.POST, instance=database)
        if form.is_valid():
            database = form.save(commit=False)
            if not form.cleaned_data['db_password']:
                database.db_password = DataBaseUser.objects.get(pk=pk).db_password
            database.save()
            if 'check_connection' in request.POST:
                try:
                    connection = psycopg2.connect(
                        dbname=database.db_name,
                        user=database.db_user,
                        password=database.db_password,
                        host=database.db_host,
                        port=database.db_port,
                        connect_timeout=connect_timeout
                    )
                    messages.success(request, f"Успешное подключение к базе данных '{database.db_name}'.", extra_tags="alert alert-success")
                    connection.close()
                except psycopg2.OperationalError:
                    messages.error(request, "Ошибка подключения! Проверьте настройки подключения.", extra_tags="alert alert-danger")
                except Exception as e:
                    messages.error(request, f"Ошибка подключения: {str(e)}", extra_tags="alert alert-danger")
            else:
                messages.success(request, "Данные успешно сохранены.", extra_tags="alert alert-success")
        else:
            messages.error(request, message="")
    else:
        form = DataBaseUserForm(instance=database)
        form.fields['db_password'].widget.attrs['value'] = database.db_password
    return render(request, template_name='projects_edit.html', context={
        'form': form,
        'database': database
    })


@login_required
def database(request, pk):
    """Информации о базе данных"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    return render(request, template_name='database.html', context={
        'database': database
    })

# @login_required
# def database_delete(request, pk):
#     """Удаление проекта базы данных"""
#     database = get_object_or_404(DataBaseUser, pk=pk)
#     database.delete()
#     messages.success(request, 'Проект успешно удален.')
#     return redirect('projects')
