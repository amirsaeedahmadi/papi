from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(DjangoUserManager):
    def _create_user(self, email, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, email, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, **extra_fields)

    def create_superuser(self, email, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            msg = "Superuser must have is_staff=True."
            raise ValueError(msg)
        if extra_fields.get("is_superuser") is not True:
            msg = "Superuser must have is_superuser=True."
            raise ValueError(msg)

        return self._create_user(email, **extra_fields)


class User(AbstractUser):
    id = models.UUIDField(primary_key=True)
    email = models.EmailField(unique=True, verbose_name=_("Email"))
    email_verified = models.BooleanField(
        verbose_name=_("Email Verified"), default=False
    )
    mobile = models.CharField(
        max_length=16,
        blank=True,
        verbose_name=_("Mobile"),
    )
    mobile_verified = models.BooleanField(
        default=False, verbose_name=_("Mobile " "Verified")
    )
    username = None
    password = None
    access_list = models.JSONField(default=list)
    roles = models.JSONField(default=list)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    @property
    def full_name(self):
        return self.get_full_name()
