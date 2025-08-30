"""
URL configuration for conf project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.contrib import admin
from django.conf.urls.static import static
from django.urls import path
from django.contrib.auth import views as auth_views
from data_generator.views import (
    home,
    register,
    logout_view,
    profile,
    profile_edit,

    projects,
    database,
    projects_edit, project_delete)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

    path('profile/', profile, name='profile'),
    path('profile_edit/', profile_edit, name='profile_edit'),

    path("projects/", projects, name="projects"),
    path("project_delete/<int:pk>/", project_delete, name="project_delete"),
    path('projects_edit/<int:pk>/', projects_edit, name='projects_edit'),


    path('database/<int:pk>/', database, name='database'),

    # path('database/<int:pk>/edit/', projects_edit, name='projects_edit'),






]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
