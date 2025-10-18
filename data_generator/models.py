from django.contrib.auth.models import AbstractUser
from django.db import models

from data_generator.db_work import db_image


class DateStamp(models.Model):
    """Временные отметки"""
    created = models.DateTimeField(verbose_name='Дата создания', auto_now_add=True)
    updated = models.DateTimeField(verbose_name='Дата изменения', auto_now=True)

    class Meta:
        abstract = True


class AppSettings(DateStamp):
    """Настройки"""
    connect_timeout_db = models.IntegerField(verbose_name="Время соединения c БД", default=5)
    view_table_db = models.IntegerField(verbose_name="Количество отображаемых данных в таблице БД", default=100)
    paginator_projects = models.IntegerField(verbose_name="Количество отображаемых проектов на странице", default=8)

    def __str__(self):
        return f'Настройки'

    class Meta:
        verbose_name = "Настройки"
        verbose_name_plural = "Настройки"


class CustomUser(AbstractUser, DateStamp):
    """Пользователь"""
    phone_number = models.CharField(verbose_name="Телефон", max_length=15, blank=True, null=True)
    position = models.CharField(verbose_name="Должность", max_length=100, blank=True, null=True)
    photo = models.ImageField(verbose_name="Изображение", upload_to='user_photo/', default='user_photo/default.png', blank=True, null=True)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"


class DataBaseName(DateStamp):
    """Подключение"""
    name = models.CharField(verbose_name="Подключение", max_length=100, unique=True)
    images_db = models.ImageField(verbose_name="Изображение", upload_to='images_db/', default='images_db/default.jpg', blank=True, null=True)

    def save(self, *args, **kwargs):
        image_mapping = db_image
        db_key = self.name.lower().strip()
        self.images_db = image_mapping.get(db_key, 'images_db/default.jpg')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Подключение"
        verbose_name_plural = "Подключение"
        ordering = 'name',


class DataBaseUser(DateStamp):
    """Проекты"""
    db_project = models.CharField(verbose_name="Проект", max_length=40, unique=True)
    db_name = models.CharField(verbose_name="Название базы данных", max_length=40)
    db_user = models.CharField(verbose_name="Пользователь", max_length=40)
    db_password = models.CharField(verbose_name="Пароль", max_length=40)
    db_host = models.CharField(verbose_name="Хост", max_length=255)
    db_port = models.CharField(verbose_name="Порт", max_length=8)
    user = models.ForeignKey(CustomUser, verbose_name="Пользователь", on_delete=models.CASCADE, related_name='data_base_user')
    data_base_name = models.ForeignKey(DataBaseName, verbose_name="Подключение", on_delete=models.CASCADE, related_name='data_base_name')

    def __str__(self):
        return f"Данные БД пользователя: {self.user.username}"

    class Meta:
        verbose_name = "Проект"
        verbose_name_plural = "Проекты"
        ordering = 'db_project',
