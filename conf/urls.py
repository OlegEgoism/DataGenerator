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
    project_create,
    projects_edit,
    project_connection,
    project_delete,

    database
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),

    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),

    path('profile/', profile, name='profile'),
    path('profile_edit/', profile_edit, name='profile_edit'),

    path("projects/", projects, name="projects"),
    path('project_create/', project_create, name='project_create'),
    path('project_edit/<int:pk>/', projects_edit, name='projects_edit'),
    path('project_connection/<int:pk>/', project_connection, name='project_connection'),
    path("project_delete/<int:pk>/", project_delete, name="project_delete"),

    path('database/<int:pk>/', database, name='database'),

    # path('database/<int:pk>/edit/', projects_edit, name='projects_edit'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
