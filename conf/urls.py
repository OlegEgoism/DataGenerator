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
from data_generator.views import home, profile, logout_view, register, edit_profile, my_projects, database_detail, database_edit

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('profile/', profile, name='profile'),

    path('my_projects/', my_projects, name='my_projects'),

    path('database/<int:pk>/', database_detail, name='database_detail'),

    path('database/<int:pk>/edit/', database_edit, name='database_edit'),

    path('profile/edit/', edit_profile, name='edit_profile'),
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
