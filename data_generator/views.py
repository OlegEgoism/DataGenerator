from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q

from data_generator.forms import CustomUserCreationForm, CustomUserForm
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