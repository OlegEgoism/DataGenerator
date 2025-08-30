from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, DataBaseUser


class CustomUserCreationForm(UserCreationForm):
    """Регистрация пользователя"""
    email = forms.EmailField(required=True, label="Email")
    photo = forms.ImageField(required=False, label="Фото")

    class Meta:
        model = CustomUser
        fields = 'username', 'email', 'photo', 'password1', 'password2'
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'password1': forms.PasswordInput(attrs={'class': 'form-control'}),
            'password2': forms.PasswordInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        existing_user = CustomUser.objects.filter(email=email).first()
        if existing_user:
            if existing_user.is_active:
                raise ValidationError("Пользователь с таким email уже зарегистрирован.")
            else:
                existing_user.delete()
        return email


class CustomUserForm(forms.ModelForm):
    """Редактирование профиля"""

    class Meta:
        model = CustomUser
        fields = ['email', 'phone_number', 'position', 'photo']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }


class DataBaseUserForm(forms.ModelForm):
    """Редактирование данных проекта"""

    class Meta:
        model = DataBaseUser
        fields = ('data_base_name', 'db_project', 'db_name', 'db_user', 'db_password', 'db_host', 'db_port')
        widgets = {
            'data_base_name': forms.Select(attrs={'class': 'form-select', 'id': 'id_data_base_name'}),
            'db_project': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название проекта'}),
            'db_name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_user': forms.TextInput(attrs={'class': 'form-control'}),
            'db_password': forms.PasswordInput(attrs={'class': 'form-control', 'id': 'id_db_password'}, render_value=True),
            'db_host': forms.TextInput(attrs={'class': 'form-control'}),
            'db_port': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['data_base_name'].empty_label = '— Выберите подключение —'
