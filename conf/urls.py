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
    project_edit,
    project_connection,
    project_delete, database_schemas, database_schemas_create, database_schemas_tables, database_schema_delete, database_schema_edit, database_schemas_tables_columns, database_schemas_tables_delete, database_schemas_tables_edit, database_schemas_tables_create,
    database_schemas_table_data, database_schemas_table_add_columns

)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    # TODO АВТОРИЗАЦИЯ/РЕГИСТРАЦИЯ
    path('register/', register, name='register'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', logout_view, name='logout'),
    # TODO ПРОФИЛЬ
    path('profile/', profile, name='profile'),
    path('profile_edit/', profile_edit, name='profile_edit'),
    # TODO ПРОЕКТ
    path("projects/", projects, name="projects"),
    path('project_create/', project_create, name='project_create'),
    path('project_edit/<int:pk>/', project_edit, name='projects_edit'),
    path('project_connection/<int:pk>/', project_connection, name='project_connection'),
    path("project_delete/<int:pk>/", project_delete, name="project_delete"),
    # TODO СХЕМЫ
    path('database_schemas/<int:pk>/', database_schemas, name='database_schemas'),
    path('database_schemas_create/<int:pk>/', database_schemas_create, name='database_schemas_create'),
    path('database_schema_delete/<int:pk>/<str:schema_name>/', database_schema_delete, name='database_schema_delete'),
    path('database_schema_edit/<int:pk>/<str:schema_name>/', database_schema_edit, name='database_schema_edit'),
    # TODO ТАБЛИЦЫ
    path('database_schemas_tables/<int:pk>/<str:schema_name>/', database_schemas_tables, name='database_schemas_tables'),
    path('database_schemas_tables_create/<int:pk>/<str:schema_name>/', database_schemas_tables_create, name='database_schemas_tables_create'),
    path('database_schemas_tables_delete/<int:pk>/<str:schema_name>/<str:table_name>/', database_schemas_tables_delete, name='database_schemas_tables_delete'),
    path('database_schemas_tables_edit/<int:pk>/<str:schema_name>/<str:table_name>/', database_schemas_tables_edit, name='database_schemas_tables_edit'),
    # TODO ПОЛЯ
    path('database_schemas_tables_columns/<int:pk>/<str:schema_name>/<str:table_name>/', database_schemas_tables_columns, name='database_schemas_tables_columns'),
    path('database_schemas_table_data/<int:pk>/<str:schema_name>/<str:table_name>/', database_schemas_table_data, name='database_schemas_table_data'),
    path('database_schemas_tables_create/<int:pk>/<str:schema_name>/', database_schemas_tables_create, name='database_schemas_tables_create'),

    path('database_schemas_table_add_columns/<int:pk>/<str:schema_name>/<str:table_name>/', database_schemas_table_add_columns, name='database_schemas_table_add_columns'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
