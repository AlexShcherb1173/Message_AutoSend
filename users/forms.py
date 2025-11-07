from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "avatar", "phone", "country")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ("email", "avatar", "phone", "country")


class EmailAuthenticationForm(AuthenticationForm):
    """Переименовываем username в email для формы логина."""
    username = forms.EmailField(label="Email")