from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(_("ФИО"), max_length=255)

    email = models.EmailField(_("Email"), unique=True)
    email_confirmed = models.BooleanField(_("Email подтвержден"), default=False)

    date_joined = models.DateTimeField(_("Зарегистрирован"), auto_now_add=True)
    is_active = models.BooleanField(_("Активный"), default=True)
    is_staff = models.BooleanField(_("Сотрудник"), default=False)

    EMAIL_FIELD = "email"
    USERNAME_FIELD = "email"

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        db_table = "user"
