from django.contrib import admin
from django.utils.safestring import mark_safe

from data_generator.models import DataBaseUser, AppSettings, CustomUser, DataBaseName

admin.site.site_header = "Генератор данных"
admin.site.site_title = "Генератор данных"


class DataBaseUserInline(admin.TabularInline):
    """Подключение"""
    model = DataBaseUser
    extra = 0
    classes = ['collapse']
    readonly_fields = 'data_base_name',


@admin.register(AppSettings)
class AppSettingsAdmin(admin.ModelAdmin):
    """Настройки"""
    list_display = '__str__', 'connect_timeout_db', 'view_table_db', 'paginator_projects', 'created', 'updated'
    list_editable = 'connect_timeout_db', 'view_table_db', 'paginator_projects',

    def has_add_permission(self, request):
        """Запрет на создание больше одной записи"""
        return not AppSettings.objects.exists()


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    """Пользователь"""
    fieldsets = (
        ('ЛИЧНЫЕ ДАННЫЕ', {
            'fields': ('username', 'preview_photo', 'photo', 'email', 'phone_number', 'position', 'last_login', 'date_joined',)},),
        ('РАЗРЕШЕНИЯ', {
            'classes': ('collapse',),
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions',)}),
    )
    list_display = 'username', 'preview_photo', 'email', 'phone_number', 'position', 'db_count', 'is_active', 'last_login', 'created', 'updated'
    list_filter = 'is_active', 'created', 'updated'
    list_editable = 'is_active',
    search_fields = 'username', 'email', 'phone_number',
    search_help_text = 'Поиск по имени пользователя, адресу электронной почте и номеру телефона'
    readonly_fields = 'last_login', 'date_joined', 'preview_photo', 'created', 'updated'
    inlines = DataBaseUserInline,
    list_per_page = 20

    def preview_photo(self, obj):
        if obj.photo:
            return mark_safe(f'<img src="{obj.photo.url}" width="80" height="80" style="border-radius: 20%;" />')
        else:
            return 'Нет фотографии'

    preview_photo.short_description = 'Фотография'

    def save_model(self, request, obj, form, change):
        """Проверка, есть ли еще один пользователь с таким же адресом электронной почты"""
        if obj.email:
            if CustomUser.objects.filter(email=obj.email).exclude(pk=obj.pk).exists():
                self.message_user(request, "Этот адрес электронной почты уже связан с другим аккаунтом", level='ERROR')
                return
        super().save_model(request, obj, form, change)

    def db_count(self, obj):
        if obj.data_base_user.count() == 0:
            return 'Нет проектов'
        else:
            return obj.data_base_user.count()

    db_count.short_description = 'Количество проектов'


@admin.register(DataBaseName)
class DataBaseNameAdmin(admin.ModelAdmin):
    """Список баз данных"""
    list_display = 'name', 'preview_images_db', 'db_count', 'created', 'updated'
    list_filter = 'name',
    readonly_fields = 'preview_images_db', 'created', 'updated'
    search_fields = 'name', 'db_project',
    search_help_text = 'Поиск по названию базы данных'
    list_per_page = 20

    def preview_images_db(self, obj):
        if obj.images_db:
            return mark_safe(f'<img src="{obj.images_db.url}" width="80" height="80" style="border-radius: 20%;" />')
        else:
            return 'Нет фотографии'

    preview_images_db.short_description = 'Фотография'

    def db_count(self, obj):
        if obj.data_base_name.count() == 0:
            return 'Нет проектов'
        else:
            return obj.data_base_name.count()

    db_count.short_description = 'Количество проектов'


@admin.register(DataBaseUser)
class DataBaseUserAdmin(admin.ModelAdmin):
    """Подключение"""
    list_display = 'db_project', 'user', 'data_base_name', 'created', 'updated'
    list_filter = 'data_base_name', 'created', 'updated'
    search_fields = 'user__username', 'db_project',
    search_help_text = 'Поиск по логину и названию проекта'
    list_per_page = 20
