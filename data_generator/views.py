import psycopg2
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from data_generator.forms import CustomUserCreationForm, CustomUserForm, DataBaseUserForm
from data_generator.models import DataBaseUser, AppSettings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages


def home(request):
    """Главная"""
    return render(request,
                  template_name='home.html')


def register(request):
    """Регистрация пользователя"""
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
    """Выход пользователя"""
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    """Профиль пользователя"""
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
def edit_profile(request):
    """Редактирование профиля пользователя"""
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
                  template_name='edit_profile.html',
                  context={'form': form})


@login_required
def my_projects(request):
    """Проекты"""
    search_query = request.GET.get("search", "").strip()
    paginator_projects = AppSettings.objects.first()
    projects = DataBaseUser.objects.filter(user=request.user)
    if search_query:
        projects = projects.filter(Q(db_project__icontains=search_query) | Q(db_name__icontains=search_query))
    projects = projects.order_by("created")
    page_size = paginator_projects.paginator_projects if paginator_projects else 4
    paginator = Paginator(projects, page_size)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request,
                  template_name="my_projects.html",
                  context={
                      "projects": page_obj,
                      "search_query": search_query})


@login_required
def database_detail(request, pk):
    """Страница информации о конкретной базе данных пользователя"""
    database = get_object_or_404(DataBaseUser, pk=pk)
    return render(request, template_name='database_detail.html', context={
        'database': database
    })


@login_required
def database_edit(request, pk):
    """Редактирование информации о базе данных и проверка подключения"""
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
    return render(request, template_name='database_edit.html', context={
        'form': form,
        'database': database
    })