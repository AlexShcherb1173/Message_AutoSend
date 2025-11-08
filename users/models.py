from __future__ import annotations
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import UploadedFile


# ============================================================
#                    ВАЛИДАТОРЫ ДЛЯ АВАТАРА
# ============================================================

ALLOWED_IMAGE_MIME = {"image/jpeg", "image/png", "image/webp"}
MAX_AVATAR_MB = 5


def validate_avatar_content(file: UploadedFile):
    """
    Проверяет MIME-тип загруженного файла.

    Разрешённые форматы:
      - JPEG (.jpg, .jpeg)
      - PNG (.png)
      - WEBP (.webp)
    """
    ctype = getattr(file, "content_type", "") or ""
    if ctype.lower() not in ALLOWED_IMAGE_MIME:
        raise ValidationError("Допустимы только изображения JPEG, PNG или WebP.")


def validate_avatar_size(file: UploadedFile):
    """
    Проверяет, чтобы размер загружаемого аватара не превышал MAX_AVATAR_MB мегабайт.
    """
    if file.size > MAX_AVATAR_MB * 1024 * 1024:
        raise ValidationError(f"Размер аватара не должен превышать {MAX_AVATAR_MB} МБ.")


# ============================================================
#                    МЕНЕДЖЕР ПОЛЬЗОВАТЕЛЯ
# ============================================================

class CustomUserManager(BaseUserManager):
    """
    Кастомный менеджер для модели User.

    Основные отличия:
      - авторизация по полю email вместо username;
      - создание суперпользователя также требует email;
      - username формируется автоматически (если не указан).
    """

    def _create_user(self, email: str, password: str | None, **extra_fields):
        """Базовый конструктор пользователя.

        Args:
            email: адрес, будет логином (уникальный).
            password: пароль (может быть None для инвайтов).
            extra_fields: прочие поля модели.

        Raises:
            ValueError: если email не указан.
        """
        if not email:
            raise ValueError("Нужно указать email")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email: str, password: str | None = None, **extra_fields):
        """Обычный пользователь: не staff, не superuser."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email: str, password: str | None, **extra_fields):
        """Суперпользователь: staff + superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser должен иметь is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser должен иметь is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

# ============================================================
#                    МОДЕЛЬ ПОЛЬЗОВАТЕЛЯ
# ============================================================

def user_avatar_upload_to(instance: "User", filename: str) -> str:
    """
    Возвращает путь для сохранения аватаров пользователей.

    """
    return f"users/{instance.pk or 'new'}/avatar/{filename}"

class User(AbstractUser):
    """
    Кастомная модель пользователя для проекта Message_AutoSend.

    Отличия от стандартной модели:
      • Авторизация по email (USERNAME_FIELD = 'email').
      • Поля username и email — уникальные.
      • Дополнительные поля:
            - avatar (ImageField)
            - phone (CharField)
            - country (CharField)
    """

    username = None

    email = models.EmailField(
        _("Email"),
        unique=True,
        db_index=True,
        help_text=_("Используется для входа в систему."),
    )

    avatar = models.ImageField(
        _("Аватар"),
        upload_to=user_avatar_upload_to,
        blank=True,
        null=True,
        validators=[validate_avatar_content, validate_avatar_size],
        help_text=_("Необязательное изображение профиля (до 5 МБ)."),
    )

    phone = models.CharField(
        _("Телефон"),
        max_length=20,
        blank=True,
        null=True,
        help_text=_("Номер телефона пользователя."),
    )

    country = models.CharField(
        _("Страна"),
        max_length=100,
        blank=True,
        null=True,
        help_text=_("Страна проживания пользователя."),
    )

    # Используем email как логин
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("Пользователь")
        verbose_name_plural = _("Пользователи")
        ordering = ("-date_joined",)

    def __str__(self) -> str:
        """Возвращает читаемое представление пользователя."""
        return self.email or self.username

    @property
    def avatar_url(self) -> str | None:
        """
        Возвращает абсолютный URL аватара (если загружен).
        Если файл не задан — возвращает None.
        """
        if self.avatar and hasattr(self.avatar, "url"):
            return self.avatar.url
        return None