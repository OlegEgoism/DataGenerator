from django.apps import AppConfig


class DataGeneratorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_generator'
    verbose_name = "Генератор данных"

